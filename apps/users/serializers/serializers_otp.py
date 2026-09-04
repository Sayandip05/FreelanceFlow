from rest_framework import serializers


class RegisterOtpInitiateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=8, required=True)
    role = serializers.ChoiceField(
        choices=["CLIENT", "FREELANCER", "client", "freelancer"],
        default="CLIENT"
    )
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")

    def validate_role(self, value):
        return value.upper()


class RegisterOtpVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(min_length=6, max_length=6, required=True)


class ResendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetOtpInitiateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetOtpVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(min_length=6, max_length=6, required=True)
    new_password = serializers.CharField(write_only=True, min_length=8, required=True)
