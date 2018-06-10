import boto3
from time import sleep

def create(server_id):

    dynamodb = boto3.resource('dynamodb')

    table = dynamodb.create_table(
        TableName=server_id,
        KeySchema=[
            {
                'AttributeName': 'player_id',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'player_id',
                'AttributeType': 'S'
            }

        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    table.meta.client.get_waiter('table_exists').wait(TableName='users')


def add_user(server_id, player_id):

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(server_id)
    table.put_item(
        Item={
            'player_id': player_id,
            'money': 10000,
        }
    )


def update_money(server_id, player_id, updated_money):

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(server_id)

    table.update_item(
        Key={
            'player_id': player_id,
        },
        UpdateExpression='SET money = :updated_money',
        ExpressionAttributeValues={
            ':updated_money': updated_money
        }
    )


def get_money(server_id, player_id):

    dynamodb = boto3.client('dynamodb')

    response = dynamodb.list_tables()

    server_exists = False

    if server_id in response['TableNames']:
        server_exists = True

    if not server_exists:
        create(server_id)
        sleep(7)
        add_user(server_id, player_id)

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(server_id)

    response = table.get_item(
        Key={
            'player_id': player_id,
        }
    )

    item = response['Item']
    return item['money']
