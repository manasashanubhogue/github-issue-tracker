import logging
import re
import requests
from datetime import datetime, timedelta
from django.views.decorators.cache import cache_page
from multiprocessing import Process, Manager
from rest_framework.response import Response
from rest_framework.views import APIView

from issue_tracker.settings import ACCESS_TOKEN

logger = logging.getLogger('django.server')


class IssueTrackerView(APIView):
    """
    API view to track issues of a given public repo
    """
    open_issues_list = []

    def update_response_list(self, resultant):
        """
        :param resultant: json response of prev page
        :param self.open_issues_list: issue list
        :param i: page count
        :return: incremented page count if next pages exists, else 0 based on response count
        """
        for val in resultant:
            if "pull_request" not in val.keys():
                if val not in self.open_issues_list:
                    self.open_issues_list.append(val['created_at'])

    def get_api_response(self, result_url, page_url):
        """
        :param page_url: end point of page count in the url
        :return: response of git api call to fetch number of open issues
        """
        # http://127.0.0.1:8000/api/get-open-issue/?url="https://api.github.com/repos/TheAlgorithms/Python"
        url = result_url + page_url + ';access_token=' + ACCESS_TOKEN
        response = requests.get(url)
        return response

    def get_first_half_response(self, first_ele, second_ele, result_url):
        for i in range(first_ele, second_ele):
            page_url = 'page=' + str(i)
            response = self.get_api_response(result_url, page_url)
            self.update_response_list(response.json())

    def get(self, request):
        """
        :param request: Contains url of github repo
        :return:
        """
        # request.url will have github url : https://github.com/TheAlgorithms/Python
        i = 1
        start_url = "https://api.github.com/repos/"

        url = request.GET.get('url').split('/')
        name = url[-2] + '/' + url[-1]
        page_url = 'page=' + str(i)
        result_url = start_url + name + '/issues?state=open;'

        response = self.get_api_response(result_url, page_url)
        if response.status_code == 200:
            last_page = 0
            """Get the last page using response headers"""
            if 'Link' in response.headers.keys():
                response_header_list = requests.utils.parse_header_links(
                    response.headers['Link'].rstrip('>').replace('>,<', ',<'))
                last_page_response = re.findall('page=\d+', response_header_list[1]['url'])
                last_page = last_page_response[0].split('page=')[1]
            initial_ele = 1
            limit = [0, 1]
            """Use multi process and manager list for faster processing"""
            if last_page not in limit:
                middle_ele = int(int(last_page) / 2)
                with Manager() as manager:
                    self.open_issues_list = manager.list()
                    processes = []
                    p = Process(target=self.get_first_half_response, args=(initial_ele, middle_ele, result_url,))
                    p.start()
                    p1 = Process(target=self.get_first_half_response,
                                 args=(middle_ele, int(last_page) + 1, result_url,))
                    p1.start()
                    processes.append(p)
                    processes.append(p1)

                    for s in processes:
                        s.join()
                    self.open_issues_list = list(self.open_issues_list)
            else:
                self.update_response_list(response.json())
        elif response.status_code == 404:
            if "message" in response.json().keys():
                data = {
                    "message": "Repository not found, or it's not public Repository. Please check"
                }
                logger.error(data)
                return Response(data, status=200)
        elif response.status_code == 403:
            if "message" in response.json().keys():
                data = {
                    "message": response.json()['message']
                }
                logger.error(data)
                return Response(data, status=200)

        issues_in_last_24_hrs = 0
        issues_between_1dayto_7day = 0
        issues_more_than_7days = 0
        difference_24_hrs = datetime.now() - timedelta(days=1)
        difference_7days = datetime.now() - timedelta(days=7)
        for created_at in self.open_issues_list:
            if created_at >= difference_24_hrs.isoformat():
                issues_in_last_24_hrs = issues_in_last_24_hrs + 1
            elif created_at <= difference_24_hrs.isoformat() and created_at >= difference_7days.isoformat():
                issues_between_1dayto_7day = issues_between_1dayto_7day + 1
        issues_more_than_7days = len(self.open_issues_list) - (issues_in_last_24_hrs + issues_between_1dayto_7day)
        result = {
            'open_issues': len(self.open_issues_list),
            'issues_in_last_24_hrs': issues_in_last_24_hrs,
            'issues_between_1dayto_7day': issues_between_1dayto_7day,
            'issues_more_than_7days': issues_more_than_7days
        }
        return Response(result, status=200)
