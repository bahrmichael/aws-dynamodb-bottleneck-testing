import json
import os
from datetime import timedelta, datetime

import boto3

from lambda_client import invoke_lambda
from util import make_chunks

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('aws-dynamodb-bottleneck-testing')


def handle(event, context):
    total_loading = 0
    total_batching = 0

    now = datetime.utcnow()
    until = (now + timedelta(minutes=5)).isoformat()

    last_evaluated_key = None

    count = 0
    # emulated do while loop
    while True:

        response, duration = load_data(until, last_evaluated_key)
        total_loading += duration

        if response['Count'] == 0:
            break
        else:
            count += response['Count']

        ids = []
        for item in response['Items']:
            ids.append(item['id'])

        start = datetime.now()
        for chunk in make_chunks(ids, 200):
            invoke_lambda(os.environ.get('SCHEDULE_FUNCTION'), json.dumps(chunk).encode('utf-8'))
        end = datetime.now()
        duration = int((end - start).total_seconds() * 1000)
        print(f"Batching {response['Count']} entries took { duration }ms.")
        total_batching += duration

        if 'LastEvaluatedKey' in response:
            print('Continuing at next page')
            last_evaluated_key = response['LastEvaluatedKey']
        else:
            print('Finished loading data')
            break

    print(f'Loading {count} entries took {total_loading}ms.')
    print(f'Batching {count} entries took {total_batching}ms.')
    print(f'Processing {count} entries took {int((datetime.now() - now).total_seconds() * 1000)}ms.')


def load_data(until, last_evaluated_key, limit=5000):
    start = datetime.now()
    if last_evaluated_key is None:
        response = table.query(
            IndexName=os.environ.get('INDEX_NAME'),
            KeyConditionExpression='#status = :st',
            ExpressionAttributeNames={"#status": "status",},
            ExpressionAttributeValues={':st': 'NEW'},
            Limit=limit,
            ProjectionExpression='id'
        )
    else:
        response = table.query(
            IndexName=os.environ.get('INDEX_NAME'),
            KeyConditionExpression='#status = :st',
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={':st': 'NEW'},
            Limit=limit,
            ProjectionExpression='id',
            ExclusiveStartKey=last_evaluated_key
        )
    end = datetime.now()
    duration = int((end - start).total_seconds() * 1000)
    print(f"Loading {response['Count']} entries took { duration }ms.")
    return response, duration
