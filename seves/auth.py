from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class CustomOIDCBackend(OIDCAuthenticationBackend):
    def get_user(self, user_id):
        """Return a user based on the id."""
        try:
            return (
                self.UserModel.objects.filter(pk=user_id)
                .select_related("agent", "agent__structure")
                .prefetch_related("groups")
                .first()
            )
        except self.UserModel.DoesNotExist:
            return None
