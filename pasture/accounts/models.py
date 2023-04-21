from django.conf import settings
from django.db import models

from pasture.accounts.managers import TradeHistoryManager
from pasture.common.behaviors import TimeStampable


class Account(TimeStampable, models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, max_length=100,
                              to_field="username", on_delete=models.DO_NOTHING, )
    account_alias = models.CharField(max_length=100, unique=True)
    account_type = models.CharField(default="NORMAL", max_length=10, choices=[
        ("NORMAL", "NORMAL"),
        ("ISA", "ISA"),
        ("PENSION", "PENSION"),
        ("IRP", "IRP"),
    ])
    is_active = models.BooleanField(default=True)
    description = models.CharField(default="", null=True, max_length=100)

    def __str__(self):
        return f"Account({self.account_alias})"


class Settlement(TimeStampable, models.Model):
    class Meta:
        unique_together = ("base_date", "account_alias")

    base_date = models.DateField(max_length=8)
    account_alias = models.ForeignKey(Account, max_length=100,
                                      db_column="account_alias", to_field="account_alias",
                                      on_delete=models.DO_NOTHING,
                                      related_name="account_settlement")

    # io
    base_io_krw = models.DecimalField(max_digits=15, decimal_places=5, null=True)
    base_io_usd = models.DecimalField(max_digits=15, decimal_places=5, null=True)
    dividend_usd = models.DecimalField(max_digits=15, decimal_places=5, null=True)
    deposit_interest_krw = models.DecimalField(max_digits=15, decimal_places=5, null=True)

    # history
    base_amount_krw = models.DecimalField(max_digits=15, decimal_places=5, null=True)
    account_evaluation_krw = models.DecimalField(max_digits=15, decimal_places=5, null=True)
    account_evaluation_usd = models.DecimalField(max_digits=15, decimal_places=5, null=True)
    stock_evaluation_krw = models.DecimalField(max_digits=15, decimal_places=5, null=True)
    stock_evaluation_usd = models.DecimalField(max_digits=15, decimal_places=5, null=True)

    # series
    exchange_rate = models.DecimalField(max_digits=8, decimal_places=3, null=True)


class OrderHistory(TimeStampable, models.Model):
    account_alias = models.ForeignKey(Account, max_length=100,
                                      db_column="account_alias", to_field="account_alias", on_delete=models.DO_NOTHING,
                                      related_name="orders")
    order_date = models.DateField(max_length=8)
    order_branch_no = models.CharField(blank=True, default="", max_length=10)
    order_no = models.CharField(blank=True, default="", max_length=10)
    origin_order_no = models.CharField(blank=True, default="", max_length=10)
    trade_type = models.CharField(blank=True, default="", max_length=2)
    trade_type_name = models.CharField(blank=True, default="", max_length=8)
    cancel_code = models.CharField(blank=True, default="", max_length=2)
    cancel_code_name = models.CharField(blank=True, default="", max_length=8)
    symbol = models.CharField(blank=True, default="", max_length=10)
    product_name = models.CharField(blank=True, default="", max_length=200)
    ord_qty = models.DecimalField(max_digits=15, decimal_places=5, null=True)
    exec_qty = models.DecimalField(max_digits=15, decimal_places=5, null=True)
    ord_price = models.DecimalField(max_digits=25, decimal_places=8, null=True)
    exec_price = models.DecimalField(max_digits=25, decimal_places=8, null=True)
    exec_amt = models.DecimalField(max_digits=25, decimal_places=8, null=True)
    unexec_qty = models.DecimalField(max_digits=15, decimal_places=5, null=True)
    status_name = models.CharField(blank=True, default="", max_length=200)
    reject_reason = models.CharField(blank=True, default="", max_length=200)
    order_time = models.CharField(blank=True, default="", max_length=6)
    market_name = models.CharField(blank=True, default="", max_length=20)
    nation_code = models.CharField(blank=True, default="", max_length=20)
    nation_name = models.CharField(blank=True, default="", max_length=20)
    market_code = models.CharField(blank=True, default="", max_length=20)
    currency_code = models.CharField(blank=True, default="", max_length=20)
    order_date_kst = models.DateField(null=True)
    order_time_kst = models.CharField(blank=True, default="", max_length=6)
    loan_code = models.CharField(blank=True, default="", max_length=2)
    channel = models.CharField(blank=True, default="", max_length=20)
    loan_date = models.CharField(blank=True, default="", max_length=20)
    reject_reason_name = models.CharField(blank=True, default="", max_length=200)

    class Meta:
        unique_together = ("order_date", "order_no", "account_alias")


class TradeHistory(TimeStampable, models.Model):
    objects = TradeHistoryManager()

    account_alias = models.ForeignKey(Account, max_length=100,
                                      db_column="account_alias", to_field="account_alias", on_delete=models.DO_NOTHING,
                                      related_name="trades")
    trade_name = models.CharField(max_length=200, help_text="거래명")
    trade_type = models.CharField(max_length=50, help_text="거래구분")
    trade_date = models.DateField(help_text="거래일자")
    trade_amt = models.DecimalField(
        default=0, max_digits=20, decimal_places=3, help_text="거래금액(세전)"
    )
    settle_amt = models.DecimalField(
        default=0, max_digits=20, decimal_places=3, help_text="정산금액(세후)"
    )
    # deposit_krw = models.IntegerField(help_text="원화잔액")
    # deposit_usd = models.DecimalField(max_digits=20, decimal_places=3, help_text="외화잔액")
    trade_qty = models.DecimalField(
        default=0, max_digits=10, decimal_places=8, help_text="거래수량"
    )
    holding_qty = models.DecimalField(
        default=0, max_digits=10, decimal_places=8, help_text="보유수량"
    )
    trade_price = models.DecimalField(
        default=0, max_digits=20, decimal_places=3, help_text="거래단가"
    )
    exchange_rate = models.DecimalField(
        default=0, max_digits=8, decimal_places=3, help_text="환율"
    )
    currency_code = models.CharField(
        max_length=5,
        help_text="환구분",
        choices=(
            ("USD", "USD"),
            ("KRW", "KRW"),
        ),
    )
    commission = models.DecimalField(
        default=0, max_digits=10, decimal_places=3, help_text="수수료"
    )
    transaction_tax = models.DecimalField(
        default=0, max_digits=10, decimal_places=3, help_text="거래세"
    )
    tax = models.DecimalField(
        default=0, max_digits=10, decimal_places=3, help_text="세금"
    )
    vat = models.DecimalField(
        default=0, max_digits=10, decimal_places=3, help_text="부가세"
    )
    repay_amt = models.DecimalField(
        default=0, max_digits=20, decimal_places=3, help_text="상환금액"
    )
    repay_profit = models.DecimalField(
        default=0, max_digits=20, decimal_places=3, help_text="상환차익"
    )
    loan_amt = models.DecimalField(
        default=0, max_digits=20, decimal_places=3, help_text="대출잔액"
    )
    symbol = models.CharField(max_length=20, null=True, help_text="상품코드")
    product_name = models.CharField(max_length=100, null=True, help_text="상품명")

    @classmethod
    def get_trade_types(cls):
        return [
            "DEPOSIT_INTEREST",
            "DEPOSIT_KRW",
            "WITHDRAW_KRW",
            "DEPOSIT_USD",
            "WITHDRAW_USD",
            "DIVIDEND_INPUT_USD",
            "EXCHANGE_USD",
        ]
