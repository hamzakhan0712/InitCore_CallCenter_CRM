import json
import logging
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Attendance, Break, BreakType, UserProfile
from django.contrib.auth.models import User
from django.utils import timezone

class UserBreakConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.group_name = f'user_{self.user_id}_breaks'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')

        if action == 'start_break':
            break_type_id = data.get('break_type_id')
            user = await self.get_user(self.user_id)
            user_profile = await self.get_user_profile(self.user_id)
            break_type = await self.get_break_type(break_type_id)

            if user and break_type:
                attendance_id = await self.get_latest_attendance_id(user_profile)
                await self.create_break(user_profile, break_type, attendance_id, active=True)
                latest_break = await self.get_latest_break()
                start_time = None

                if latest_break:
                    start_time = timezone.localtime(latest_break.start_time).strftime('%Y-%m-%d %H:%M:%S')

                user_name = user.get_full_name()
                user_role = user_profile.role

                if user_profile.role == 'Agent':
                    team_leader_id = await sync_to_async(user_profile.get_team_leader_id)()

                    if team_leader_id:
                        team_leader_group = f'team_leader_{team_leader_id}_breaks'
                        await self.channel_layer.group_send(
                            team_leader_group,
                            {
                                'type': 'break_started',
                                'user_id': self.user_id,
                                'user_name': user_name,
                                'user_role': user_role,
                                'break_type': break_type.name,
                                'start_time': start_time,
                            }
                        )

                await self.channel_layer.group_send(
                    'admin_breaks',
                    {
                        'type': 'break_started',
                        'user_id': self.user_id,
                        'user_name': user_name,
                        'user_role': user_role,
                        'break_type': break_type.name,
                        'start_time': start_time,
                    }
                )

        elif action == 'end_break':
            user = await self.get_user(self.user_id)
            user_profile = await self.get_user_profile(self.user_id)
            break_obj = await self.get_last_active_break(user_profile)

            if break_obj:
                break_obj.end_time = timezone.localtime(timezone.now())
                break_obj.active = False
                await sync_to_async(break_obj.save)()

                await self.channel_layer.group_send(
                    'admin_breaks',
                    {
                        'type': 'break_ended',
                        'user_id': self.user_id,
                    }
                )

                team_leader_id = await sync_to_async(user_profile.get_team_leader_id)()
                if team_leader_id:
                    team_leader_group = f'team_leader_{team_leader_id}_breaks'
                    await self.channel_layer.group_send(
                        team_leader_group,
                        {
                            'type': 'break_ended',
                            'user_id': self.user_id,
                        }
                    )

    async def break_started(self, event):
        await self.send(text_data=json.dumps({
            'on_break': True,
            'break_type': event['break_type'],
            'start_time': event['start_time'],
        }))

    async def break_ended(self, event):
        await self.send(text_data=json.dumps({
            'on_break': False,
        }))

    async def get_user(self, user_id):
        try:
            return await sync_to_async(User.objects.get)(id=user_id)
        except User.DoesNotExist:
            return None

    async def get_user_profile(self, user_id):
        try:
            return await sync_to_async(UserProfile.objects.get)(user__id=user_id)
        except UserProfile.DoesNotExist:
            return None

    async def get_break_type(self, break_type_id):
        try:
            return await sync_to_async(BreakType.objects.get)(id=break_type_id)
        except BreakType.DoesNotExist:
            return None

    async def create_break(self, user_profile, break_type, attendance_id, active=True):
        await sync_to_async(Break.objects.create)(
            user=user_profile, break_type=break_type, attendance_id=attendance_id, active=active
        )

    async def get_latest_attendance_id(self, user_profile):
        try:
            latest_attendance = await sync_to_async(
                Attendance.objects.filter(user=user_profile).latest)('id')
            return latest_attendance.id
        except Attendance.DoesNotExist:
            return None

    async def get_last_active_break(self, user_profile):
        try:
            return await sync_to_async(Break.objects.filter(
                user=user_profile, active=True, end_time=None).latest)('id')
        except Break.DoesNotExist:
            return None

    async def get_latest_break(self):
        try:
            return await sync_to_async(Break.objects.latest)('id')
        except Break.DoesNotExist:
            return None



class AllBreaksConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        if self.user.is_superuser:
            self.group_name = 'admin_breaks'
        else:
            self.user_profile = await sync_to_async(UserProfile.objects.get)(user=self.user)
            if self.user_profile.role == 'Team Leader':
                self.group_name = f'team_leader_{self.user.id}_breaks'
            else:
                await self.close()
                return

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def break_started(self, event):
        await self.send(text_data=json.dumps({
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'user_role': event['user_role'],
            'on_break': True,
            'break_type': event['break_type'],
            'start_time': event['start_time'],
        }))

    async def break_ended(self, event):
        await self.send(text_data=json.dumps({
            'user_id': event['user_id'],
            'on_break': False,
        }))

    async def get_recent_breaks(self):
        try:
            if self.user.is_superuser:
                recent_breaks = await sync_to_async(list)(
                    Break.objects.filter(active=True).values(
                        'user_id', 'user__full_name', 'user__role', 'break_type__name', 'start_time'
                    )
                )
            elif self.user_profile.role == 'Team Leader':
                recent_breaks = await sync_to_async(list)(
                    Break.objects.filter(active=True, user__assigned_to=self.user).values(
                        'user_id', 'user__full_name', 'user__role', 'break_type__name', 'start_time'
                    )
                )

            return [{
                'user_id': b['user_id'],
                'user_name': b['user__full_name'],
                'user_role': b['user__role'],
                'break_type': b['break_type__name'],
                'start_time': timezone.localtime(b['start_time']).strftime('%Y-%m-%d %H:%M:%S'),
                'on_break': True,
            } for b in recent_breaks]
        except Exception as e:
            return []
















