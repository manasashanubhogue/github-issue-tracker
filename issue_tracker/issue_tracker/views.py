from rest_framework.views import APIView
from django.http.response import HttpResponse
import requests
from datetime import datetime, timedelta
from rest_framework.response import Response
import logging

logger = logging.getLogger('django.server')
class IssueTrackerView(APIView):
    """
    API view to track issues of a given public repo
    """
    def update_response_list(self, resultant, open_issues_list, i):
        """
        :param resultant: json response of prev page
        :param open_issues_list: issue list
        :param i: page count
        :return: incremented page count if next pages exists, else 0 based on response count
        """
        for val in resultant:
            if "pull_request" not in val.keys():
                if val not in open_issues_list:
                    open_issues_list.append(val)
        if len(resultant) >= 30:
            i = i + 1
            return i
        else:
            return 0

    def get_api_response(self, result_url, page_url):
        """
        :param page_url: end point of page count in the url
        :return: response of git api call to fetch number of open issues
        """

        url = result_url+ page_url
        response = requests.get(url)
        return response

    def get(self, request):
        """
        :param request: Contains url of github repo
        :return:
        """
        # request.url will have github url : https://github.com/TheAlgorithms/Python

        i = 1
        open_issues_list = []
        start_url = "https://api.github.com/repos/"

        url = request.GET.get('url').split('/')
        print(url)
        name = url[-2]+ '/' + url[-1]
        page_url = 'page=' + str(i)
        result_url = start_url + name + '/issues?state=open;'

        response = self.get_api_response(result_url, page_url)
        if response.status_code == 200:
            resultant = response.json()
            if len(resultant) > 0:
                while page_url:
                    response = self.get_api_response(result_url, page_url)
                    i = self.update_response_list(resultant, open_issues_list, i)
                    if i == 0:
                        break
                    else:
                        page_url = 'page=' + str(i)
                        resultant = response.json()
        elif response.status_code == 404:
            if "message" in response.json().keys():
                data = {
                    "message" : "Repository not found, or it's not public Repository. Please check"
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
        for val in open_issues_list:
            if val['created_at'] >= difference_24_hrs.isoformat():
                issues_in_last_24_hrs = issues_in_last_24_hrs + 1
            elif val['created_at'] <= difference_24_hrs.isoformat() and val[
                'created_at'] >= difference_7days.isoformat():
                issues_between_1dayto_7day = issues_between_1dayto_7day + 1
        issues_more_than_7days = len(open_issues_list) - (issues_in_last_24_hrs + issues_between_1dayto_7day)
        result = {
            'open_issues': len(open_issues_list),
            'issues_in_last_24_hrs': issues_in_last_24_hrs,
            'issues_between_1dayto_7day': issues_between_1dayto_7day,
            'issues_more_than_7days': issues_more_than_7days
        }
        return Response(result, status=200)





