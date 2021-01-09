from pyramid.settings import asbool

BOOL_SETTINGS = [
    "broker_connection_retry",
    "broker_use_ssl",
    "elasticsearch_retry_on_timeout",
    "elasticsearch_save_meta_as_text",
    "enable_utc",
    "redis_backend_use_ssl",
    "redis_retry_on_timeout",
    "redis_socket_keepalive",
    "result_backend_always_retry",
    "result_extended",
    "result_persistent",
    "task_acks_late",
    "task_acks_on_failure_or_timeout",
    "task_always_eager",
    "task_create_missing_queues",
    "task_default_rate_limit",
    "task_eager_propagates",
    "task_ignore_result",
    "task_inherit_parent_priority",
    "task_publish_retry",
    "task_reject_on_worker_lost",
    "task_remote_tracebacks",
    "task_send_sent_event",
    "task_store_errors_even_if_ignored",
    "task_track_started",
    "worker_direct",
    "worker_disable_rate_limits",
    "worker_enable_remote_control",
    "worker_hijack_root_logger",
    "worker_log_color",
    "worker_pool_restarts",
    "worker_redirect_stdouts",
    "worker_send_task_events",
]


INT_SETTINGS = [
    "beat_max_loop_interval",
    "beat_sync_every",
    "broker_connection_max_retries",
    "broker_pool_limit",
    "broker_transport_options.max_retries",
    "broker_transport_options.visibility_timeout",
    "cassandra_port",
    "elasticsearch_max_retries",
    "redis_max_connections",
    "result_backend_base_sleep_between_retries_ms",
    "result_backend_max_retries",
    "result_backend_max_sleep_between_retries_ms",
    "result_cache_max",
    "result_expires",
    "task_default_priority",
    "task_protocol",
    "task_publish_retry_policy.max_retries",
    "task_queue_max_priority",
    "worker_concurrency",
    "worker_max_memory_per_child",
    "worker_max_tasks_per_child",
    "worker_prefetch_multiplier",
]


FLOAT_SETTINGS = [
    "azureblockblob_retry_increment_base",
    "azureblockblob_retry_initial_backoff_sec",
    "azureblockblob_retry_max_attempts",
    "broker_connection_timeout",
    "broker_heartbeat",
    "broker_heartbeat_checkrate",
    "control_queue_expires",
    "control_queue_ttl",
    "elasticsearch_timeout",
    "event_queue_expires",
    "event_queue_ttl",
    "redis_socket_connect_timeout",
    "redis_socket_timeout",
    "result_chord_join_timeout",
    "result_chord_retry_interval",
    "task_publish_retry_policy.interval_max",
    "task_publish_retry_policy.interval_start",
    "task_publish_retry_policy.interval_step",
    "task_soft_time_limit",
    "task_time_limit",
    "worker_lost_wait",
    "worker_proc_alive_timeout",
    "worker_timer_precision",
]


LIST_SETTINGS = [
    "accept_content",
    "cassandra_servers",
    "imports",
    "include",
    "result_accept_content",
]


def extract_celery_settings(settings):
    celery_settings = dict()
    filtered = (
        (k[7:], v) for (k, v) in settings.items() if k.startswith("celery.")
    )
    for key, value in filtered:
        *parts, final_part = key.split(".")
        location = celery_settings
        for part in parts:
            location = location.setdefault(part, dict())
        if key in BOOL_SETTINGS:
            value = asbool(value)
        elif key in INT_SETTINGS:
            value = int(value)
        elif key in FLOAT_SETTINGS:
            value = float(value)
        elif key in LIST_SETTINGS:
            value = [x.strip() for x in value.split(",")]
        location[final_part] = value
    return celery_settings
