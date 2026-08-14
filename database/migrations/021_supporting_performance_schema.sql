-- ALIF ERP - Supporting & Performance schema verification
-- This migration documents the final supporting/performance architecture.
-- No physical consolidated_points table is created because the current
-- performance/reporting services calculate consolidated points with CTEs
-- from approved module records.

DO $$
DECLARE
    required_table TEXT;
    missing TEXT := '';
    required_tables TEXT[] := ARRAY[
        'speaker_forum_attendance',
        'portion_completion',
        'mentoring_notes',
        'student_leave_requests',
        'staff_attendance',
        'staff_leave_requests',
        'notifications',
        'achievements',
        'audit_logs'
    ];
BEGIN
    FOREACH required_table IN ARRAY required_tables LOOP
        IF to_regclass(current_schema() || '.' || required_table) IS NULL THEN
            missing := missing || CASE WHEN missing = '' THEN '' ELSE ', ' END || required_table;
        END IF;
    END LOOP;

    IF missing <> '' THEN
        RAISE EXCEPTION 'ALIF ERP supporting schema incomplete. Missing tables: %', missing;
    END IF;
END $$;

-- Performance uses approved module rows directly. Keep this marker explicit
-- so future maintainers do not add a redundant consolidated_points table.
