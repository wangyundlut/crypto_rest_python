# coding=utf-8
import json

class huobiException(Exception):

    def __init__(self, response):
        print(response.text + ', ' + str(response.status_code))
        self.code = 0
        try:
            json_res = response.json()
        except ValueError:
            self.message = 'Invalid JSON error message from huobi: {}'.format(response.text)
        else:
            if "error_code" in json_res.keys() and "error_message" in json_res.keys():
                self.code = json_res['error_code']
                self.message = json_res['error_message']
            else:
                self.code = 'None'
                self.message = 'System error'

        self.status_code = response.status_code
        self.response = response
        self.request = getattr(response, 'request', None)

    def __str__(self):  # pragma: no cover
        return 'API Request Error(error_code=%s): %s' % (self.code, self.message)


class huobiRequestException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'huobiRequestException: %s' % self.message


class huobiParamsException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'huobiParamsException: %s' % self.message
