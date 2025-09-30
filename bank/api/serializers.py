from rest_framework import serializers

from bank.models import Transaction


class TransactionQuerySerializer(serializers.Serializer):
    date_from = serializers.DateTimeField(required=False, allow_null=True)
    date_to = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, data):
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError("date_from cannot be later than date_to")
        return data


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['amount', 'transaction_type', 'created_at']
        read_only_fields = ['amount', 'transaction_type', 'created_at']


class TransferSerializer(serializers.Serializer):
    receiver_account_number = serializers.CharField(max_length=10)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value

    def validate_receiver_account_number(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError("Invalid account number")
        return value
