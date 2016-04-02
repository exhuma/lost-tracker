def get_email(oauth_response):
    from facebook import GraphAPI
    api = GraphAPI(access_token=oauth_response['access_token'], version='2.5')
    response = api.request('/me', args={'fields': 'email'})
    return response['email']


def get_image_url(connection):
    from facebook import GraphAPI
    api = GraphAPI(access_token=connection.access_token, version='2.5')
    response = api.request('/%s/picture' % connection.provider_user_id,
                           args={'redirect': '1',
                                 'type': 'large'})
    return 'data:%s;base64,%s' % (response['mime-type'], response['data'].encode('base64'))
