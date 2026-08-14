-- ALIF ERP production schema gate.
-- This migration intentionally does not create application tables.
-- It fails fast if the canonical base schema has not been installed.
DO $$
DECLARE
    required_table TEXT;
    missing TEXT := '';
    required_tables TEXT[] := ARRAY[
        'institutions','roles','users','academic_years','classes','subjects',
        'students','staff_classes','staff_subjects',
        'attendance','exams','exam_subjects','exam_marks','reading_submissions',
        'writing_submissions','speaking_submissions','publications',
        'language_skill_assessments','achievements','paper_presentations',
        'staff_attendance','staff_leave_requests','portion_completion',
        'mentoring_notes','student_leave_requests','student_promotions',
        'notifications','speaker_forum_attendance','audit_logs'
    ];
BEGIN
    FOREACH required_table IN ARRAY required_tables LOOP
        IF to_regclass(current_schema() || '.' || required_table) IS NULL THEN
            missing := missing || CASE WHEN missing = '' THEN '' ELSE ', ' END || required_table;
        END IF;
    END LOOP;

    IF missing <> '' THEN
        RAISE EXCEPTION 'ALIF ERP production schema incomplete. Missing tables: %', missing;
    END IF;
END $$;
