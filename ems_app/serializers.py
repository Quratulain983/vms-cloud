from rest_framework import serializers

from .models import (
    E1,
    E2,
    Analyzer,
    Box,
    Com1,
    Com2,
    Data,
    Device,
    Gateway,
    Gateways,
    Hardware,
    MetaData,
    Project,
    Project_Manager,
    Sensor,
    SensorGateway,
    User,
    User_Project,
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}} # Important for security

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'

class UserProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = User_Project
        fields = '__all__'

class HardwareSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hardware
        fields = '__all__'

class GatewaysSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gateways
        fields = '__all__'

class DataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Data
        fields = '__all__'

class ProjectManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project_Manager
        fields = '__all__'

class BoxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Box
        fields = '__all__'

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'

class GatewaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Gateway
        fields = '__all__'

class Com1Serializer(serializers.ModelSerializer):
    class Meta:
        model = Com1
        fields = '__all__'

class Com2Serializer(serializers.ModelSerializer):
    class Meta:
        model = Com2
        fields = '__all__'

class E1Serializer(serializers.ModelSerializer):
    class Meta:
        model = E1
        fields = '__all__'

class E2Serializer(serializers.ModelSerializer):
    class Meta:
        model = E2
        fields = '__all__'

class AnalyzerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analyzer
        fields = '__all__'

class MetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaData
        fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaData
        fields = '__all__'

class InvoiceTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaData
        fields = '__all__'

class admincrSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaData
        fields = '__all__'

class superadmincrSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetaData
        fields = '__all__'


class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = "__all__"


class GatewaySerializer(serializers.ModelSerializer):
    sensors = SensorSerializer(many=True, read_only=True)

    class Meta:
        model = SensorGateway
        fields = "__all__"
