from django.db import models

# Create your models here.


class PartnerExpenses(models.Model):
    """
    CREATE TABLE expenses (
      id bigserial PRIMARY KEY,
      partner_id text,
      expense_type text,
      expense_amount text,
      customer_user_id bigserial REFERENCES customer_users (user_id) ON UPDATE CASCADE # optional
      customer_id text
      created_at timestamp,
      updated_at timestamp
    );
    """
    pass
