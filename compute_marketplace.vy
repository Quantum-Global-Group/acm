# @version ^0.3.10
# Agent-to-Agent Compute Marketplace Smart Contract
# Arc EVM-compatible L1
# USDC is the settlement asset

# Interface for USDC token
interface IERC20:
    def transfer(to: address, amount: uint256) -> bool: nonpayable
    def transferFrom(sender: address, to: address, amount: uint256) -> bool: nonpayable
    def balanceOf(holder: address) -> uint256: view
    def approve(spender: address, amount: uint256) -> bool: nonpayable

usdc_token: public(IERC20)
owner: public(address)

# Agent balance tracking (1 USDC = 10^6 wei)
agent_balances: public(HashMap[address, uint256])

# Max unit price = $0.01 expressed in USDC's smallest unit (10,000 = 0.01 USDC)
max_unit_price: public(uint256)

# Counter for accounting / monitoring
total_payments: public(uint256)
total_volume: public(uint256)


event Deposit:
    agent: indexed(address)
    amount: uint256

event Withdrawal:
    agent: indexed(address)
    amount: uint256

event PaymentSettled:
    consumer: indexed(address)
    provider: indexed(address)
    amount: uint256
    timestamp: uint256
    task_id: String[256]

event UsageRecorded:
    consumer: indexed(address)
    provider: indexed(address)
    quantity: uint256
    unit_price: uint256
    total_cost: uint256

event MaxUnitPriceUpdated:
    old_price: uint256
    new_price: uint256


@external
def __init__(usdc_address: address):
    """Initialize with USDC token address on Arc."""
    self.usdc_token = IERC20(usdc_address)
    self.owner = msg.sender
    self.max_unit_price = 10000  # $0.01 in 6-decimal USDC units


@external
def deposit(amount: uint256):
    """Deposit USDC into the agent's marketplace balance."""
    assert amount > 0, "Deposit amount must be > 0"
    assert self.usdc_token.transferFrom(msg.sender, self, amount), "Transfer failed"
    self.agent_balances[msg.sender] += amount
    log Deposit(msg.sender, amount)


@external
def withdraw(amount: uint256):
    """Withdraw USDC from the agent's marketplace balance."""
    assert amount > 0, "Withdrawal amount must be > 0"
    assert self.agent_balances[msg.sender] >= amount, "Insufficient balance"
    self.agent_balances[msg.sender] -= amount
    assert self.usdc_token.transfer(msg.sender, amount), "Transfer failed"
    log Withdrawal(msg.sender, amount)


@internal
def _settle_payment(
    consumer: address,
    provider: address,
    quantity: uint256,
    unit_price: uint256,
    task_id: String[256]
) -> bool:
    """Internal payment settlement used by both single and batch entry points."""
    if quantity == 0:
        return False
    if unit_price == 0 or unit_price > self.max_unit_price:
        return False
    if provider == empty(address) or consumer == empty(address):
        return False
    if consumer == provider:
        return False

    total_cost: uint256 = quantity * unit_price
    if self.agent_balances[consumer] < total_cost:
        return False

    self.agent_balances[consumer] -= total_cost
    self.agent_balances[provider] += total_cost

    self.total_payments += 1
    self.total_volume += total_cost

    log PaymentSettled(consumer, provider, total_cost, block.timestamp, task_id)
    log UsageRecorded(consumer, provider, quantity, unit_price, total_cost)
    return True


@external
def pay_for_compute(
    consumer: address,
    provider: address,
    quantity: uint256,
    unit_price: uint256,
    task_id: String[256]
) -> bool:
    """
    Atomic per-action payment from consumer to provider.
    Reverts on validation failure (single-call semantics).
    """
    assert quantity > 0, "Quantity must be > 0"
    assert unit_price > 0, "Unit price must be > 0"
    assert unit_price <= self.max_unit_price, "Unit price exceeds $0.01 limit"
    assert provider != empty(address), "Provider address is invalid"
    assert consumer != empty(address), "Consumer address is invalid"
    assert consumer != provider, "Consumer and provider must be different"

    total_cost: uint256 = quantity * unit_price
    assert self.agent_balances[consumer] >= total_cost, "Consumer has insufficient balance"

    self.agent_balances[consumer] -= total_cost
    self.agent_balances[provider] += total_cost

    self.total_payments += 1
    self.total_volume += total_cost

    log PaymentSettled(consumer, provider, total_cost, block.timestamp, task_id)
    log UsageRecorded(consumer, provider, quantity, unit_price, total_cost)
    return True


# Batch payment uses parallel arrays instead of an unsupported tuple DynArray.
@external
def batch_payments(
    consumers: DynArray[address, 256],
    providers: DynArray[address, 256],
    quantities: DynArray[uint256, 256],
    unit_prices: DynArray[uint256, 256],
    task_ids: DynArray[String[256], 256]
) -> uint256:
    """
    Process up to 256 payments in a single tx for efficiency.
    Skips individually invalid entries; returns count of successful settlements.
    """
    n: uint256 = len(consumers)
    assert n == len(providers), "providers length mismatch"
    assert n == len(quantities), "quantities length mismatch"
    assert n == len(unit_prices), "unit_prices length mismatch"
    assert n == len(task_ids), "task_ids length mismatch"

    count: uint256 = 0
    for i in range(256):
        if i >= n:
            break
        if self._settle_payment(
            consumers[i], providers[i], quantities[i], unit_prices[i], task_ids[i]
        ):
            count += 1
    return count


@external
@view
def get_balance(agent: address) -> uint256:
    """Return on-marketplace USDC balance for an agent (in 6-decimal units)."""
    return self.agent_balances[agent]


@external
@view
def get_balances_batch(agents: DynArray[address, 256]) -> DynArray[uint256, 256]:
    """Batch read balances for monitoring."""
    balances: DynArray[uint256, 256] = []
    for agent in agents:
        balances.append(self.agent_balances[agent])
    return balances


@external
def set_max_unit_price(new_max_price: uint256):
    """Owner can adjust the per-action price ceiling."""
    assert msg.sender == self.owner, "Only owner can set price limit"
    assert new_max_price > 0, "Max price must be > 0"
    old_price: uint256 = self.max_unit_price
    self.max_unit_price = new_max_price
    log MaxUnitPriceUpdated(old_price, new_max_price)
