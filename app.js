const DATA_FILE = "./data/Wastewater Data-Table 1.csv";

// Page elements
const seasonFilter = document.getElementById("season-filter");
const pathogenFilter = document.getElementById("pathogen-filter");
const labFilter = document.getElementById("lab-filter");
const searchInput = document.getElementById("search-input");

const recordCount = document.getElementById("record-count");
const siteCount = document.getElementById("site-count");
const detectedCount = document.getElementById("detected-count");
const outlierCount = document.getElementById("outlier-count");

const tableBody = document.getElementById("table-body");
const status = document.getElementById("status");
const chartCanvas = document.getElementById("concentration-chart");

// Data
let allData = [];
let chart = null;

// Load CSV
async function init() {
  try {
    const response = await fetch(DATA_FILE);

    if (!response.ok) {
      throw new Error(`Could not load CSV: ${response.status}`);
    }

    const rows = parseCSV(await response.text());

    const headerIndex = rows.findIndex(row =>
      row[0]?.trim() === "respiratory_season" &&
      row[1]?.trim() === "pathogen"
    );

    if (headerIndex === -1) {
      throw new Error("Could not find the CSV headers.");
    }

    const headers = rows[headerIndex].map(value => value.trim());

    allData = rows
      .slice(headerIndex + 1)
      .filter(row => row.some(value => value.trim() !== ""))
      .map(row => {
        const record = {};

        headers.forEach((header, index) => {
          // Ignore an empty header caused by a trailing comma.
          if (header) {
            record[header] = (row[index] ?? "").trim();
          }
        });

        return record;
      });

    populateFilters();
    applyFilters();
  } catch (error) {
    console.error(error);
    status.textContent = error.message;
  }
}

// Parse CSV, including quoted commas and line breaks.
function parseCSV(text) {
  const rows = [];
  let row = [];
  let cell = "";
  let quoted = false;

  text = text.replace(/^\uFEFF/, "");

  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    const next = text[i + 1];

    if (char === '"') {
      if (quoted && next === '"') {
        cell += '"';
        i++;
      } else {
        quoted = !quoted;
      }
    } else if (char === "," && !quoted) {
      row.push(cell);
      cell = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && next === "\n") {
        i++;
      }

      row.push(cell);
      rows.push(row);

      row = [];
      cell = "";
    } else {
      cell += char;
    }
  }

  if (quoted) {
    throw new Error("CSV contains an unclosed quoted field.");
  }

  if (cell.length > 0 || row.length > 0) {
    row.push(cell);
    rows.push(row);
  }

  return rows;
}

// Populate dropdowns.
function populateFilters() {
  addOptions(seasonFilter, "respiratory_season");
  addOptions(pathogenFilter, "pathogen");
  addOptions(labFilter, "testing_lab");
}

function addOptions(select, column) {
  const values = [...new Set(
    allData.map(row => row[column]).filter(Boolean)
  )].sort();

  values.forEach(value => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
}

// Apply filters and update the dashboard.
function applyFilters() {
  const season = seasonFilter.value;
  const pathogen = pathogenFilter.value;
  const lab = labFilter.value;
  const query = searchInput.value.toLowerCase().trim();

  const filteredData = allData.filter(row => {
    const matchesSeason =
      !season || row.respiratory_season === season;

    const matchesPathogen =
      !pathogen || row.pathogen === pathogen;

    const matchesLab =
      !lab || row.testing_lab === lab;

    const matchesSearch =
      !query ||
      Object.values(row).some(value =>
        value.toLowerCase().includes(query)
      );

    return (
      matchesSeason &&
      matchesPathogen &&
      matchesLab &&
      matchesSearch
    );
  });

  updateMetrics(filteredData);
  renderChart(filteredData);
  renderTable(filteredData);
}

// Update summary cards.
function updateMetrics(data) {
  recordCount.textContent = data.length.toLocaleString();

  const sites = new Set(
    data.map(row => row.sampling_location).filter(Boolean)
  );

  siteCount.textContent = sites.size.toLocaleString();

  detectedCount.textContent = data.filter(
    row => row.detect_status.toLowerCase() === "detected"
  ).length.toLocaleString();

  outlierCount.textContent = data.filter(
    row => row.is_outlier.toLowerCase() === "true"
  ).length.toLocaleString();
}

// Draw the concentration chart.
function renderChart(data) {
  const grouped = {};

  data.forEach(row => {
    const date = row.sample_collection_date;
    const value = Number(row.concentration_copies_per_l);

    if (
      !date ||
      row.concentration_copies_per_l === "" ||
      !Number.isFinite(value)
    ) {
      return;
    }

    if (!grouped[date]) {
      grouped[date] = [];
    }

    grouped[date].push(value);
  });

  const dates = Object.keys(grouped).sort();

  const averages = dates.map(date => {
    const values = grouped[date];

    return values.reduce((sum, value) => sum + value, 0)
      / values.length;
  });

  if (chart) {
    chart.destroy();
    chart = null;
  }

  // The table and filters still work if Chart.js is unavailable.
  if (typeof Chart === "undefined") {
    return;
  }

  chart = new Chart(chartCanvas, {
    type: "line",

    data: {
      labels: dates,
      datasets: [{
        label: "Mean concentration (copies/L)",
        data: averages,
        borderColor: "#2563eb",
        backgroundColor: "rgba(37, 99, 235, 0.12)",
        borderWidth: 2,
        pointRadius: 2,
        tension: 0.2,
        fill: true
      }]
    },

    options: {
      responsive: true,
      maintainAspectRatio: false,

      scales: {
        x: {
          title: {
            display: true,
            text: "Collection date"
          }
        },

        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Concentration (copies/L)"
          }
        }
      }
    }
  });
}

// Display the first 500 matching records.
function renderTable(data) {
  tableBody.replaceChildren();

  data.slice(0, 500).forEach(row => {
    const tr = document.createElement("tr");

    const values = [
      row.sample_collection_date,
      row.pathogen,
      row.pathogen_target,
      row.organization,
      row.testing_lab,
      row.detect_status,
      row.concentration_copies_per_l
    ];

    values.forEach(value => {
      const td = document.createElement("td");
      td.textContent = value ?? "";
      tr.appendChild(td);
    });

    tableBody.appendChild(tr);
  });

  const shown = Math.min(data.length, 500);

  status.textContent =
    `Showing ${shown.toLocaleString()} of ` +
    `${data.length.toLocaleString()} matching records` +
    (data.length > 500 ? " (first 500 shown)" : "");
}

// Update the dashboard when a filter changes.
seasonFilter.addEventListener("change", applyFilters);
pathogenFilter.addEventListener("change", applyFilters);
labFilter.addEventListener("change", applyFilters);
searchInput.addEventListener("input", applyFilters);

init();
