# Scheduled Discovery Automation Guide

## Overview

The Scheduled Discovery system enables automated, hands-free lead discovery that runs on configurable schedules. Businesses can set up recurring discovery jobs targeting specific cities, states, countries, industries, or categories.

## Architecture

### Components

1. **DiscoveryScheduleService** (`app/services/discovery_schedule_service.py`)
   - CRUD operations for schedules and targets
   - Discovery execution orchestration
   - Query building and target rotation

2. **Celery Workers** (`app/workers/scheduled_discovery.py`)
   - `check_and_run_scheduled_discoveries`: Runs every 5 minutes, checks for due schedules
   - `run_discovery_for_schedule`: Executes discovery for a specific schedule
   - `trigger_manual_discovery`: Manually trigger a schedule run

3. **Celery Beat Configuration** (`app/workers/celery_app.py`, `celeryconfig.py`)
   - Periodic task scheduler
   - Beat schedule: checks every 5 minutes

## Key Features

### Schedule Types
- **HOURLY**: Run every N hours (configurable via `interval_hours`)
- **DAILY**: Run once per day at the same time
- **WEEKLY**: Run once per week
- **CUSTOM**: Custom cron expression (planned)

### Target Types
- **CITY**: Discover businesses in a specific city ("New York", "Los Angeles")
- **STATE**: Discover businesses in a state ("California", "Texas")
- **COUNTRY**: Discover businesses in a country ("USA", "Canada")
- **INDUSTRY**: Discover businesses by industry ("Technology", "Healthcare")
- **CATEGORY**: Discover businesses by category ("Restaurant", "Retail Store")

### Discovery Limits
- `max_leads_per_run`: Maximum leads to discover per execution (default: 50)
- Target priority: Higher priority targets are processed first
- Concurrency: Max 3 concurrent discovery runs

## Usage Examples

### 1. Create a Schedule

```python
from app.services.discovery_schedule_service import DiscoveryScheduleService

schedule_data = {
    "name": "NYC Restaurants Discovery",
    "description": "Daily discovery of restaurants in New York",
    "is_active": True,
    "schedule_type": "DAILY",
    "max_leads_per_run": 50,
}

schedule = DiscoveryScheduleService.create_schedule(schedule_data, db)
```

### 2. Add Targets

```python
# Add a city target
target1 = DiscoveryScheduleService.add_target(
    str(schedule.id),
    {
        "target_type": "CITY",
        "target_value": "New York",
        "priority": 10,
    },
    db
)

# Add a category target
target2 = DiscoveryScheduleService.add_target(
    str(schedule.id),
    {
        "target_type": "CATEGORY",
        "target_value": "Restaurant",
        "priority": 5,
    },
    db
)
```

### 3. List Schedules

```python
# List all active schedules
schedules = DiscoveryScheduleService.list_schedules(db, active_only=True)

for schedule in schedules:
    print(f"{schedule.name}: {len(schedule.targets)} targets")
    print(f"  Next run: {schedule.next_run_at}")
    print(f"  Last run: {schedule.last_run_at}")
```

### 4. Update Schedule

```python
updated = DiscoveryScheduleService.update_schedule(
    str(schedule.id),
    {
        "max_leads_per_run": 100,
        "is_active": True,
    },
    db
)
```

### 5. Manual Trigger

```python
from app.workers.scheduled_discovery import trigger_manual_discovery

# Trigger a schedule manually (bypasses next_run_at check)
result = trigger_manual_discovery.delay(str(schedule.id))
```

## Running Celery Workers

### Start Worker

```bash
# Windows
celery -A app.workers.celery_app worker --loglevel=info --pool=solo --concurrency=1

# Linux/Mac
celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
```

### Start Beat Scheduler

```bash
# Start Celery Beat (periodic task scheduler)
celery -A app.workers.celery_app beat --loglevel=info
```

### Combined Worker + Beat (Development)

```bash
# Run both worker and beat in one process
celery -A app.workers.celery_app worker --beat --loglevel=info --pool=solo
```

## Monitoring

### Check Task Status

```python
from celery.result import AsyncResult

# Get task result
result = AsyncResult(task_id)
print(f"Status: {result.status}")
print(f"Result: {result.result}")
```

### View Beat Schedule

```python
from app.workers.celery_app import celery_app

# Display configured beat schedule
for name, config in celery_app.conf.beat_schedule.items():
    print(f"{name}: {config['task']} every {config['schedule']}s")
```

### Registered Tasks

All registered Celery tasks:

1. `app.workers.scheduled_discovery.check_and_run_scheduled_discoveries`
2. `app.workers.scheduled_discovery.run_discovery_for_schedule`
3. `app.workers.scheduled_discovery.trigger_manual_discovery`
4. `app.workers.tasks.execute_discovery_job`
5. `app.workers.tasks.publish_scheduled_social_posts`
6. `app.workers.tasks.sync_social_metrics_task`

## Database Schema

### DiscoverySchedule
- `id`: UUID primary key
- `name`: Schedule name
- `description`: Optional description
- `is_active`: Whether schedule is active
- `schedule_type`: HOURLY, DAILY, WEEKLY, CUSTOM
- `cron_expression`: For CUSTOM schedules
- `interval_hours`: For HOURLY schedules
- `max_leads_per_run`: Discovery limit per execution
- `last_run_at`: Last execution timestamp
- `next_run_at`: Next scheduled execution

### DiscoveryTarget
- `id`: UUID primary key
- `schedule_id`: Foreign key to DiscoverySchedule
- `target_type`: CITY, STATE, COUNTRY, INDUSTRY, CATEGORY
- `target_value`: Target value (e.g., "New York")
- `priority`: Processing priority (higher first)

### DiscoveryRun
- `id`: UUID primary key
- `schedule_id`: Foreign key to DiscoverySchedule
- `status`: RUNNING, COMPLETED, FAILED
- `leads_discovered`: Number of leads found
- `target_snapshot`: JSON snapshot of targets at execution time
- `error_message`: Error details if failed
- `started_at`: Start timestamp
- `completed_at`: Completion timestamp

## Configuration

### Environment Variables

```env
# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/crm_leads
```

### Beat Schedule Configuration

In `app/workers/celery_app.py`:

```python
celery_app.conf.beat_schedule = {
    'check-scheduled-discoveries': {
        'task': 'app.workers.scheduled_discovery.check_and_run_scheduled_discoveries',
        'schedule': 300.0,  # Every 5 minutes
    },
}
```

## Error Handling

### Retry Logic
- Failed discovery runs retry up to 3 times
- 5-minute delay between retries
- Exponential backoff

### Concurrency Control
- Maximum 3 concurrent discoveries
- Excess schedules are skipped and retried on next beat cycle

### Error Logging
- All errors logged with full traceback
- Discovery run status tracked in database
- Error messages stored in DiscoveryRun.error_message

## Best Practices

1. **Set Realistic Limits**: Use `max_leads_per_run` to avoid rate limiting
2. **Prioritize Targets**: Assign higher priority to important targets
3. **Monitor Execution**: Check `last_run_at` and `next_run_at` regularly
4. **Review Run History**: Query DiscoveryRun records for performance insights
5. **Adjust Schedules**: Modify schedule_type and interval based on results

## Testing

Run the test script:

```bash
python test_discovery_schedule.py
```

Expected output:
```
✅ Created schedule
✅ Added targets
✅ Listed schedules
✅ Got next target
✅ Updated schedule
✅ Built queries
✅ Cleaned up test data
✅ All tests passed!
```

## Troubleshooting

### Issue: Tasks not running
- Verify Celery worker is running
- Check Beat scheduler is active
- Confirm schedule is active (`is_active=True`)
- Verify `next_run_at` is in the past

### Issue: No leads discovered
- Check targets are configured
- Verify discovery providers are configured
- Review error messages in DiscoveryRun records

### Issue: Too many concurrent runs
- Default limit is 3 concurrent discoveries
- Increase `MAX_CONCURRENT_DISCOVERIES` in `scheduled_discovery.py`
- Or adjust schedule frequencies to spread execution

## API Integration (Coming Soon)

Future API endpoints for scheduled discovery:

- `POST /api/v1/discovery/schedules` - Create schedule
- `GET /api/v1/discovery/schedules` - List schedules
- `GET /api/v1/discovery/schedules/{id}` - Get schedule details
- `PUT /api/v1/discovery/schedules/{id}` - Update schedule
- `DELETE /api/v1/discovery/schedules/{id}` - Delete schedule
- `POST /api/v1/discovery/schedules/{id}/targets` - Add target
- `DELETE /api/v1/discovery/targets/{id}` - Remove target
- `POST /api/v1/discovery/schedules/{id}/trigger` - Manual trigger
- `GET /api/v1/discovery/runs` - List discovery runs
- `GET /api/v1/discovery/runs/{id}` - Get run details

## Performance Metrics

Typical performance:
- Schedule check cycle: ~1-2 seconds
- Discovery execution: 30-120 seconds (depends on limit and targets)
- Database operations: <100ms per operation
- Concurrent executions: 3 simultaneous schedules

## Future Enhancements

1. **Custom Cron Expressions**: Full croniter integration for complex schedules
2. **Target Rotation**: Round-robin target selection across runs
3. **Performance Analytics**: Track discovery quality and conversion rates
4. **Smart Scheduling**: AI-powered schedule optimization
5. **Webhook Notifications**: Alert on completion/failure
6. **Advanced Filters**: Target criteria by revenue, employees, etc.
