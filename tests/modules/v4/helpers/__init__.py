import json


def make_user(client, version, market):
    user_url = '/{}/{}/user/create'.format(version, market)
    result = client.get(user_url)
    return result.json['Hash']


def make_colony(client, version, market, user_id):
    colony = {'BaseName': 'TestBase',
              'FactionName': 'TestFaction',
              'Planet': 'TestPlanet',
              'OwnerType': 'Steam',
              'OwnerID': user_id,
              'LastGameTick': 0,
              'HasSpawned': False}

    url = '/{}/{}/colonies/create'.format(version, market)

    result = client.put(url, data=json.dumps(colony), mimetype='application/json')

    return result.json['Hash']


def make_prime(client, version, market, colony_id):
    # Get token
    url = '/{}/{}/prime_subscription/check/{}'.format(version, market, colony_id)
    result = client.get(url, mimetype='application/json')

    url = '/{}/{}/prime_subscription/subscribe/{}'.format(version, market, colony_id)
    post = {'Token': result.json['Token']}
    client.put(url, data=json.dumps(post), mimetype='application/json')


def get_vanilla_thing_data():
    with open('./tests/modules/v4/helpers/vanilla_thing_list.json') as data:
        vanilla_thing_data = json.load(data)
    return vanilla_thing_data
