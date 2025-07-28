export const mockData = [
  {
    application: "App 1",
    line: "Line 1",
    product: "Party Pack",
    reason: "Missing Coding",
    quantity: 10,
    date: "01-02-2025",
  },
  {
    application: "App 2",
    line: "Line 2",
    product: "Tub",
    reason: "Incorrect Price",
    quantity: 12,
    date: "02-02-2025",
  },
  {
    application: "App 3",
    line: "Line 1",
    product: "Party Pack",
    reason: "Missing Coding",
    quantity: 8,
    date: "03-02-2025",
  },
  {
    application: "App 1",
    line: "Line 3",
    product: "Tub",
    reason: "Missing Coding",
    quantity: 15,
    date: "04-02-2025",
  },
  {
    application: "App 2",
    line: "Line 2",
    product: "Party Pack",
    reason: "Incorrect Price",
    quantity: 7,
    date: "05-02-2025",
  },
  {
    application: "App 3",
    line: "Line 1",
    product: "Tub",
    reason: "Incorrect Price",
    quantity: 11,
    date: "06-12-2024",
  },
  {
    application: "App 1",
    line: "Line 3",
    product: "Party Pack",
    reason: "Incorrect Price",
    quantity: 9,
    date: "07-02-2025",
  },
  {
    application: "App 2",
    line: "Line 1",
    product: "Tub",
    reason: "Missing Coding",
    quantity: 14,
    date: "08-02-2025",
  },
];

// Extract unique filter options
export const applications = [
  ...new Set(mockData.map((item) => item.application)),
].map((app) => ({ label: app, value: app }));

export const lines = [...new Set(mockData.map((item) => item.line))].map(
  (line) => ({
    label: line,
    value: line,
  })
);
export const reasons = [...new Set(mockData.map((item) => item.reason))].map(
  (reason) => ({ label: reason, value: reason })
);

export const dateRanges = [
  { label: "Toute la période", value: null},
  { label: "Last Week", value: 7 },
  { label: "Last Month", value: 30 },
  { label: "Last 3 Months", value: 90 },
  { label: "Last 6 Months", value: 180 },
  { label: "Last Year", value: 365 },
];
