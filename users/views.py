from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model, authenticate
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
import secrets
import datetime

from .serializers import (
    RegisterSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Compte créé avec succès."}, status=201)
        return Response(serializer.errors, status=400)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, username=email, password=password)
        if not user:
            return Response({"error": "Email ou mot de passe incorrect."}, status=401)

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                token = secrets.token_urlsafe(32)
                user.reset_token = token
                user.reset_token_expiry = timezone.now() + datetime.timedelta(minutes=30)
                user.save()

                send_mail(
                    subject="Réinitialisation de mot de passe",
                    message=f"Ton token de réinitialisation : {token}\nValide 30 minutes.",
                    from_email=None,
                    recipient_list=[email],
                )
            except User.DoesNotExist:
                pass  # sécurité : ne pas révéler si l'email existe

        return Response({"message": "Si l'email existe, un lien a été envoyé."})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']

            try:
                user = User.objects.get(reset_token=token)
                if user.reset_token_expiry < timezone.now():
                    return Response({"error": "Token expiré."}, status=400)

                user.set_password(new_password)
                user.reset_token = None
                user.reset_token_expiry = None
                user.save()
                return Response({"message": "Mot de passe mis à jour avec succès."})

            except User.DoesNotExist:
                return Response({"error": "Token invalide."}, status=400)

        return Response(serializer.errors, status=400)