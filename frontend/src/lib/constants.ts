export interface BranchDefinition {
  id: string;
  name: string;
  locationType: string;
  dailyTargetInr: number;
}

export const ASSAM_BRANCHES: readonly BranchDefinition[] = [
  {
    id: "BR001",
    name: "Kamakhya Gate Branch",
    locationType: "Transit hub",
    dailyTargetInr: 58000,
  },
  {
    id: "BR002",
    name: "Dharapur Branch",
    locationType: "Suburban residential",
    dailyTargetInr: 52000,
  },
  {
    id: "BR003",
    name: "Azara Branch",
    locationType: "Hospital perimeter",
    dailyTargetInr: 64000,
  },
  {
    id: "BR004",
    name: "Rani Gate Branch",
    locationType: "Residential edge",
    dailyTargetInr: 48000,
  },
];

export const THERAPEUTIC_CATEGORIES: readonly string[] = [
  "Analgesic",
  "Antiallergic",
  "Antibiotic",
  "Antidiabetic",
  "Antiemetic",
  "Antifungal",
  "Antigout",
  "Antipyretic",
  "Antiseptic",
  "Antispasmodic",
  "Cardiovascular",
  "Endocrine",
  "Gastrointestinal",
  "Hepatoprotective",
  "Laxative",
  "Nutritional",
  "Ophthalmic",
  "Probiotic",
  "Respiratory",
];

export function getBranchLabel(branchId: string): string {
  if (branchId === "ALL") {
    return "All branches (Assam network)";
  }
  const match = ASSAM_BRANCHES.find((b) => b.id === branchId);
  return match ? `${match.name} (${match.id})` : branchId;
}
