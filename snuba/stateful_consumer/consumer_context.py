<< << << < HEAD
from snuba.consumer_initializer import ConsumerBuiler
from snuba.stateful_consumer import StateData, StateType, StateOutput
== == == =
from batching_kafka_consumer import BatchingKafkaConsumer
from typing import Sequence

from snuba.stateful_consumer import StateData, StateType, StateCompletionEvent
>>>>>> > feat / performBootstrap
from snuba.stateful_consumer.state_context import StateContext
from snuba.stateful_consumer.states.bootstrap import BootstrapState
from snuba.stateful_consumer.states.consuming import ConsumingState
from snuba.stateful_consumer.states.paused import PausedState
from snuba.stateful_consumer.states.catching_up import CatchingUpState


class ConsumerContext(StateContext[StateType, StateCompletionEvent, StateData]):
    """
    Context class for the stateful consumer. The states defined here
    regulate when the consumer is consuming from the main topic and when
    it is consuming from the control topic.
    """

    def __init__(
        self,
        consumer_builder: ConsumerBuiler,
        group_id: str,
        bootstrap_servers: Sequence[str],
        control_topic: str,
    ) -> None:
        bootstrap_state = BootstrapState(
            topic,
            bootstrap_servers,
            group_id,
        )
        super(ConsumerContext, self).__init__(
            definition={
                StateType.BOOTSTRAP: (bootstrap_state, {
                    StateCompletionEvent.NO_SNAPSHOT: StateType.CONSUMING,
                    StateCompletionEvent.SNAPSHOT_INIT_RECEIVED: StateType.SNAPSHOT_PAUSED,
                    StateCompletionEvent.SNAPSHOT_READY_RECEIVED: StateType.CATCHING_UP,
                }),
                StateType.CONSUMING: (ConsumingState(consumer_builder), {
                    StateCompletionEvent.CONSUMPTION_COMPLETED: None,
                    StateCompletionEvent.SNAPSHOT_INIT_RECEIVED: StateType.SNAPSHOT_PAUSED,
                }),
                StateType.SNAPSHOT_PAUSED: (PausedState(), {
                    StateCompletionEvent.CONSUMPTION_COMPLETED: None,
                    StateCompletionEvent.SNAPSHOT_READY_RECEIVED: StateType.CATCHING_UP,
                }),
                StateType.CATCHING_UP: (CatchingUpState(consumer_builder), {
                    StateCompletionEvent.CONSUMPTION_COMPLETED: None,
                    StateCompletionEvent.SNAPSHOT_CATCHUP_COMPLETED: StateType.CONSUMING,
                }),
            },
            start_state=StateType.BOOTSTRAP,
        )
