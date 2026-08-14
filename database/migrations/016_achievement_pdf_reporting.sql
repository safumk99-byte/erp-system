-- ALIF ERP
-- Phase 32: Achievement PDF reporting support
-- Reporting-only indexes; scoring remains governed by 010_achievement_enhancements.sql.

CREATE INDEX IF NOT EXISTS idx_achievements_student_status_date
    ON achievements (institution_id, student_id, status, achievement_date DESC);

CREATE INDEX IF NOT EXISTS idx_achievements_student_type_status
    ON achievements (institution_id, student_id, achievement_type, status);

-- Never expose unapproved points through reporting aggregates.
UPDATE achievements
SET points = 0, bonus_points = 0
WHERE status <> 'Approved'
  AND (COALESCE(points, 0) <> 0 OR COALESCE(bonus_points, 0) <> 0);
