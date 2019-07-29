from uuid import uuid4

import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('aws-dynamodb-bottleneck-testing')


def run():
    target = 250000
    with table.batch_writer() as batch:
        for i in range(1, target + 1):
            batch.put_item(
                Item={
                    'id': str(uuid4()),
                    'status': 'NEW',
                    'date': str(uuid4()),
                    'payload': str(uuid4()),
                    'target': str(uuid4()),
                    'user': str(uuid4())
                }
            )
            if i % 100 == 0:
                print(f'{i}/{target}')


if __name__ == '__main__':
    run()
