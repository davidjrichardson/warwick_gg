from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class UWCSAccount(ProviderAccount):
    def to_str(self):
        dflt = super(UWCSAccount, self).to_str()
        return self.account.extra_data.get('nickname', dflt)


class UWCSProvider(OAuth2Provider):
    id = 'uwcs'
    name = 'UWCS'
    account_class = UWCSAccount

    def extract_uid(self, data):
        return str(data['id'])

    def extract_common_fields(self, data):
        return dict(
            uni_id=data.get('uni_id'),
            email=data.get('email'),
            nickname=data.get('nickname'),
            name=data.get('full_name')
        )

    def get_default_scope(self):
        return ['lanapp']


provider_classes = [UWCSProvider]
