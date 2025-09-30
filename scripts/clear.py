from peer_loan.models import *


loans = Loan.objects.all().delete()
transactions = LoanTransaction.objects.all().delete()


# docker compose exec -it drf python manage.py shell --command "exec(open('scripts/clear.py').read())"