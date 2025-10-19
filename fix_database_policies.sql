-- 修复 invoices 表的 RLS 策略
-- 这个脚本会删除旧策略并创建正确的策略

-- 1. 删除可能存在的旧策略
DROP POLICY IF EXISTS "allow anon insert" ON public.invoices;
DROP POLICY IF EXISTS "allow anon select" ON public.invoices;
DROP POLICY IF EXISTS "allow anon update" ON public.invoices;
DROP POLICY IF EXISTS "allow anon delete" ON public.invoices;

-- 2. 创建新的正确策略

-- 允许匿名用户插入数据 (不使用 USING 子句)
CREATE POLICY "allow anon insert"
ON public.invoices
FOR INSERT
TO anon
WITH CHECK (true);

-- 允许所有人读取数据
CREATE POLICY "allow anon select"
ON public.invoices
FOR SELECT
TO anon, authenticated
USING (true);

-- 允许匿名用户更新数据
CREATE POLICY "allow anon update"
ON public.invoices
FOR UPDATE
TO anon
USING (true)
WITH CHECK (true);

-- 允许匿名用户删除数据
CREATE POLICY "allow anon delete"
ON public.invoices
FOR DELETE
TO anon
USING (true);

-- 验证策略已创建
SELECT
    schemaname,
    tablename,
    policyname,
    cmd as operation,
    roles
FROM pg_policies
WHERE tablename = 'invoices'
ORDER BY policyname;
