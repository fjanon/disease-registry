ALTER TABLE dmd_diagnosis ADD COLUMN "created" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();
ALTER TABLE dmd_diagnosis ADD COLUMN "updated" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();
