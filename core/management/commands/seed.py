"""`python manage.py seed` - idempotent rich demo data + skato superuser."""
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Note, Project, Task

DEMO_PASSWORD = "TaskSitePass!23"  # nosec B105 - demo-only fixture password
ADMIN_USERNAME = "skato"
ADMIN_PASSWORD = "root"  # nosec B105 - per project requirements


class Command(BaseCommand):
    help = "Create the skato superuser and a rich set of demo projects/tasks/notes."

    def handle(self, *args, **options):
        today = timezone.localdate()

        # --- Superuser (set_password bypasses validators; OK for ORM bootstrap) ---
        admin, _ = User.objects.get_or_create(
            username=ADMIN_USERNAME,
            defaults={"email": "skato@tasksite.local"},
        )
        admin.is_staff = admin.is_superuser = True
        admin.email = "skato@tasksite.local"
        admin.set_password(ADMIN_PASSWORD)
        admin.save()
        self.stdout.write(self.style.SUCCESS(
            f"Superuser ready: {ADMIN_USERNAME} / {ADMIN_PASSWORD}"
        ))

        # --- Demo team members ---
        members = {}
        for uname, email in [
            ("alice",  "alice@example.com"),
            ("bob",    "bob@example.com"),
            ("carol",  "carol@example.com"),
            ("daniel", "daniel@example.com"),
        ]:
            u, _ = User.objects.get_or_create(username=uname, defaults={"email": email})
            u.set_password(DEMO_PASSWORD)
            u.save()
            members[uname] = u
        alice, bob, carol, daniel = (
            members["alice"], members["bob"], members["carol"], members["daniel"]
        )

        # --- Project blueprints ---
        plans = [
            {
                "title": "Tasksite Web Launch",
                "description": (
                    "Public launch of the Tasksite web app: marketing site, "
                    "production deployment, monitoring and on-call rota."
                ),
                "priority": Project.Priority.HIGH,
                "due": today + timedelta(days=21),
                "owner": admin,
                "members": [alice, bob, carol],
                "tasks": [
                    ("Finalise landing page copy",
                     "Write hero, features and FAQ. Get sign-off from product.",
                     False, [alice], today + timedelta(days=3)),
                    ("Provision production database",
                     "Set up managed Postgres, automated backups, restore drill.",
                     True, [bob], today - timedelta(days=2)),
                    ("Configure HTTPS + HSTS preload",
                     "Issue cert, set HSTS to 1y, submit to preload list.",
                     False, [admin, bob], today + timedelta(days=7)),
                    ("Run security review checklist",
                     "OWASP Top 10 walkthrough, fix any findings before launch.",
                     False, [admin, carol], today + timedelta(days=10)),
                    ("Set up status page + on-call",
                     "Public status page + rotating PagerDuty schedule.",
                     False, [carol], today + timedelta(days=14)),
                ],
            },
            {
                "title": "Q3 Research Sprint",
                "description": (
                    "Three-week research sprint: literature review, prototype, "
                    "evaluation and a written report for the supervisor."
                ),
                "priority": Project.Priority.MEDIUM,
                "due": today + timedelta(days=30),
                "owner": alice,
                "members": [admin, daniel],
                "tasks": [
                    ("Literature review",
                     "Survey 15-20 recent papers on secure web frameworks.",
                     True, [alice], today - timedelta(days=5)),
                    ("Prototype experiment harness",
                     "Reproducible Docker setup with seeded data.",
                     False, [daniel], today + timedelta(days=6)),
                    ("Run benchmark suite",
                     "Compare CSP enforcement modes; capture timing data.",
                     False, [daniel, alice], today + timedelta(days=12)),
                    ("Draft results section",
                     "Tables + charts for the report.",
                     False, [alice], today + timedelta(days=20)),
                ],
            },
            {
                "title": "Internal Wiki Migration",
                "description": (
                    "Move the team wiki off the legacy server, deduplicate "
                    "articles, and lock down editing permissions."
                ),
                "priority": Project.Priority.LOW,
                "due": today + timedelta(days=45),
                "owner": bob,
                "members": [carol, daniel],
                "tasks": [
                    ("Export legacy wiki",
                     "Use the export tool, verify all attachments come across.",
                     True, [bob], today - timedelta(days=10)),
                    ("Audit and dedupe articles",
                     "Identify stale pages older than 18 months and archive.",
                     False, [carol], today + timedelta(days=14)),
                    ("Set up role-based ACLs",
                     "Public read, members write, admins delete.",
                     False, [bob], today + timedelta(days=25)),
                ],
            },
            {
                "title": "Customer Onboarding Revamp",
                "description": (
                    "Rebuild the new-customer onboarding flow to cut "
                    "time-to-first-value from one week to one day."
                ),
                "priority": Project.Priority.HIGH,
                "due": today + timedelta(days=12),
                "owner": carol,
                "members": [admin, alice, bob],
                "tasks": [
                    ("Map current onboarding journey",
                     "Document every step + drop-off points.",
                     True, [carol], today - timedelta(days=8)),
                    ("Design new welcome email sequence",
                     "Five emails over the first three days.",
                     False, [carol, alice], today + timedelta(days=4)),
                    ("Build in-app product tour",
                     "Highlights core features on first login.",
                     False, [admin, bob], today + timedelta(days=9)),
                    ("Measure activation lift",
                     "A/B test for two weeks; report results.",
                     False, [carol], today + timedelta(days=30)),
                ],
            },
        ]

        # --- Apply blueprints idempotently ---
        for plan in plans:
            project, created = Project.objects.get_or_create(
                title=plan["title"],
                defaults={
                    "description": plan["description"],
                    "owner": plan["owner"],
                    "priority": plan["priority"],
                    "due_date": plan["due"],
                },
            )
            project.members.set(plan["members"])
            if created:
                for title, body, done, assignees, due in plan["tasks"]:
                    t = Task.objects.create(
                        project=project, title=title, body=body,
                        completed=done, due_date=due,
                    )
                    t.assignees.set(assignees)

        # --- A handful of notes for visual richness ---
        if not Note.objects.exists():
            launch = Project.objects.get(title="Tasksite Web Launch")
            sec_task = launch.tasks.filter(title__icontains="security review").first()
            if sec_task:
                Note.objects.create(
                    task=sec_task, author=admin,
                    title="Threat-model checklist",
                    body=("Cover: AuthN/Z, IDOR, SSRF, XSS, CSRF, file upload, "
                          "secret handling, dependency CVEs, logging hygiene."))
                Note.objects.create(
                    task=sec_task, author=carol,
                    title="External pentest scheduled",
                    body="Vendor confirmed for the week of launch-1. NDA signed.")

            research = Project.objects.get(title="Q3 Research Sprint")
            lit = research.tasks.filter(title__icontains="Literature").first()
            if lit:
                Note.objects.create(
                    task=lit, author=alice,
                    title="Key references",
                    body=("Most relevant: Django security docs, OWASP ASVS 4.0, "
                          "Mozilla Observatory methodology."))

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {Project.objects.count()} projects, "
            f"{Task.objects.count()} tasks, "
            f"{Note.objects.count()} notes."
        ))
        self.stdout.write(self.style.WARNING(
            f"Demo team password: {DEMO_PASSWORD}"
        ))
