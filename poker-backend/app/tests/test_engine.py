import pytest
import unittest.mock
from app.engine.fsm import PokerFSM
from app.engine.rng import DeterministicRNG

@pytest.mark.asyncio
async def test_fsm_initial_state():
    # Mock pg_client to avoid DB connection in unit test
    with unittest.mock.patch('app.storage.pg.pg_client.connect', new_callable=unittest.mock.AsyncMock), \
         unittest.mock.patch('app.storage.pg.pg_client.log_hand', new_callable=unittest.mock.AsyncMock):
        fsm = PokerFSM("test-table")
        assert fsm.state.phase == "waiting"
        assert fsm.state.pot == 0

@pytest.mark.asyncio
async def test_rng_determinism():
    rng1 = DeterministicRNG(12345)
    rng2 = DeterministicRNG(12345)
    
    assert rng1.randint(0, 100) == rng2.randint(0, 100)
    
    deck1 = list(range(52))
    deck2 = list(range(52))
    
    rng1.shuffle(deck1)
    rng2.shuffle(deck2)
    
    assert deck1 == deck2
