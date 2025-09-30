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
