"""Serializers del motor de juego (HU-13)."""

from rest_framework import serializers

from apps.games.models import Game, GameMode, Team, Turn, TurnStatus


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["id", "name", "avatar", "score", "streak"]
        read_only_fields = ["id", "score", "streak"]


class TeamInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=20)
    avatar = serializers.CharField(max_length=8, allow_blank=True, required=False)


class GameCreateSerializer(serializers.Serializer):
    """Entrada para crear una partida (HU-13)."""

    mode = serializers.ChoiceField(choices=GameMode.choices)
    config = serializers.DictField(required=False, default=dict)
    teams = TeamInputSerializer(many=True)

    def validate_teams(self, value: list[dict]) -> list[dict]:
        if len(value) < 2:
            raise serializers.ValidationError("Se requieren al menos dos equipos.")
        names = [t["name"] for t in value]
        if len(names) != len(set(names)):
            raise serializers.ValidationError(
                "Los nombres de equipo no pueden repetirse."
            )
        return value


class GameSerializer(serializers.ModelSerializer):
    teams = TeamSerializer(many=True, read_only=True)

    class Meta:
        model = Game
        fields = [
            "id",
            "mode",
            "config",
            "status",
            "teams",
            "started_at",
            "finished_at",
        ]
        read_only_fields = fields


class TurnCreateSerializer(serializers.Serializer):
    """Entrada para crear un turno."""

    team_id = serializers.IntegerField()
    movie_id = serializers.IntegerField()
    scene_number = serializers.IntegerField(min_value=1)


class TurnResultSerializer(serializers.Serializer):
    """Entrada para registrar el resultado de un turno (HU-13, HU-21, HU-22)."""

    status = serializers.ChoiceField(choices=TurnStatus.choices)
    time_used = serializers.IntegerField(min_value=0)
    speed_bonus_threshold = serializers.IntegerField(min_value=0)
    stolen_by_id = serializers.IntegerField(required=False, allow_null=True)


class TurnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Turn
        fields = [
            "id",
            "game",
            "team",
            "movie",
            "scene_number",
            "status",
            "time_used",
            "speed_bonus",
            "stolen_by",
        ]
        read_only_fields = ["id", "speed_bonus", "stolen_by"]


class GameResultTeamSerializer(serializers.ModelSerializer):
    """Desglose de resultados por equipo (HU-29)."""

    guessed = serializers.IntegerField(read_only=True)
    failed = serializers.IntegerField(read_only=True)
    steals = serializers.IntegerField(read_only=True)

    class Meta:
        model = Team
        fields = ["id", "name", "avatar", "score", "guessed", "failed", "steals"]
