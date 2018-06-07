# coding: utf-8
"""
Created on 28.05.18
@author: Eugeny Kurkovich
"""
import os
import json
import argparse
import pathlib

from flex.core import load, validate_api_call, validate
from utils.session import ScalrApiSession


API_HOST = "7540b07cd110.test-env.scalr.com"
API_KEY = "yr0vbbu0fEly5ri/vIamdYW2qXYUxCsQE50TzLXy"
API_KEY_ID = "APIKEKVUERR0MBZ9VYIW"

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("test_specification", help="Path to test specification in json format")
    parser.add_argument("swagger_definitions", help="Path to api requests swagger definitions in yaml format")
    args = parser.parse_args()
    test_spec_path = pathlib.Path(args.test_specification)
    req_spec_path = pathlib.Path(args.swagger_definitions)
    if test_spec_path.absolute().exists():
        with open(test_spec_path.absolute().as_posix(), 'r') as f:
            spec = json.load(f)
            api_session = ScalrApiSession(
                API_HOST,
                API_KEY_ID,
                API_KEY
            )
            resp = api_session.request(**spec)
            print(resp.json())
            if req_spec_path.absolute().exists():
                schema = load(req_spec_path.absolute().as_posix())
                validation_res = validate(schema, resp.json())
                validation_res = validate_api_call(schema, raw_request=resp.request, raw_response=resp)



