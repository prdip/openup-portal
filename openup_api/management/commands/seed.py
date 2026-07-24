from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils import timezone

# Import Models here
from openup_app.models import UserRole, Registration, JobsType

'''Seeds the lookup tables (user roles, job statuses) and a demo client
   and employee account. Safe to re-run: existing rows are left alone.'''

# ROLE IDS ARE HARDCODED THROUGHOUT THE VIEWS (user_role_id=1 / user_role_id=2)
# SO THEY ARE PINNED HERE INSTEAD OF LETTING AUTOFIELD ASSIGN THEM
USER_ROLES = (
    (1, 'employee'),
    (2, 'client'),
    (3, 'admin'),
)

# 1==> ACTIVE 2==> ACCEPTED 3==> COMPLETED 4==> CANCELED 5==> NOT COMPLETED
JOB_STATUSES = (
    (1, 'active'),
    (2, 'accepted'),
    (3, 'completed'),
    (4, 'canceled'),
    (5, 'not completed'),
)

DEMO_PASSWORD = 'Openup@123'

DEMO_USERS = (
    {
        'user_first_name'   :   'Demo',
        'user_last_name'    :   'Client',
        'user_email'        :   'client@openup.test',
        'user_phone_number' :   '9000000001',
        'role_id'           :   2,
        'user_status'       :   1,
        'employee_status'   :   0,
    },
    {
        'user_first_name'   :   'Demo',
        'user_last_name'    :   'Employee',
        'user_email'        :   'employee@openup.test',
        'user_phone_number' :   '9000000002',
        'role_id'           :   1,
        'user_status'       :   1,      # EMPLOYEE CANNOT LOG IN UNLESS ACTIVATED BY ADMIN
        'employee_status'   :   1,
    },
)


class Command(BaseCommand):
    help = 'seed user roles, job statuses and demo client/employee accounts'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        now = timezone.now()

        # USER ROLES
        for role_id, role_name in USER_ROLES:
            role, created = UserRole.objects.get_or_create(
                role_id=role_id,
                defaults={
                    'role_name'         :   role_name,
                    'role_status'       :   True,
                    'role_created_at'   :   now,
                    'role_is_delete'    :   False,
                },
            )
            self.report('role', role_id, role_name, created)

        # JOB STATUSES
        for status_id, status_name in JOB_STATUSES:
            status, created = JobsType.objects.get_or_create(
                status_id=status_id,
                defaults={'status_name': status_name},
            )
            self.report('job status', status_id, status_name, created)

        # DEMO USERS
        for row in DEMO_USERS:
            data = dict(row)
            role_id = data.pop('role_id')
            email = data['user_email']

            user, created = Registration.objects.get_or_create(
                user_email=email,
                user_role_id=role_id,
                user_is_delete=0,
                defaults=dict(
                    data,
                    user_password=make_password(DEMO_PASSWORD),
                    user_is_verified=1,
                    create_at=now,
                ),
            )
            self.report('user', user.user_id, email, created)

        self.stdout.write(self.style.SUCCESS(
            '\nseeding complete -- demo login password is %s' % DEMO_PASSWORD
        ))

    def report(self, label, pk, name, created):
        action = 'created' if created else 'exists '
        style = self.style.SUCCESS if created else self.style.WARNING
        self.stdout.write(style('  %s %s %s: %s' % (action, label, pk, name)))
