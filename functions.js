const districts = ["Barcelona", "Ciutat_Vella", "Eixample", "Sants_Montjuic", "Les_Corts", "Sarria_Sant_Gervasi", "Gracia", "Horta_Guinardo", "Nou_Barris", "Sant_Andreu", "Sant_Marti"];

const defaultUser = "PA";
const defaultDistrict = "Barcelona";

let currentUser = defaultUser;
let currentDistrict = defaultDistrict;

/* Navigate user */
function navigate(user) {
  // We only update the user part of the hash, keeping the district
  updateURL(user, currentDistrict);
}

/* Select district */
function selectDistrict(district) {
  updateURL(currentUser, district);
  
  // Scroll to the top of the page smoothly
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  });
}

/* Update URL */
function updateURL(user, district) {
  window.location.hash = `${user}/${district}`;
}

/* Read URL */
function readURL() {
  const hash = window.location.hash.replace("#", "");

  if (!hash) {
    currentUser = defaultUser;
    currentDistrict = defaultDistrict;
    return;
  }

  const parts = hash.split("/");
  currentUser = parts[0] || defaultUser;
  currentDistrict = parts[1] || defaultDistrict;
}

/* Render everything */
function render() {
  readURL();

  // 1. Highlight User Buttons in Header
  const userButtons = document.querySelectorAll(".user-nav button");
  userButtons.forEach(btn => {
    if (btn.textContent.trim() === currentUser) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  // 2. Update Main Content Images
  const mainPicElem = document.getElementById("main_pic");
  if (mainPicElem) {
    mainPicElem.src = `plots/${currentUser}/${currentDistrict}-${currentUser}.png`;
  }

  const tableStatsElem = document.getElementById("table_stats");
  if (tableStatsElem) {
    tableStatsElem.src = `stats/${currentUser}/stats-${currentDistrict}-${currentUser}.png`;
  }

  const timeseriesElem = document.getElementById("timeseries");
  if (timeseriesElem) {
    if ( currentUser = "comparison" ){
      timeseriesElem.src = `plots/${currentUser}/timeseries/${currentDistrict}.png`;
    } else {
      timeseriesElem.src = `plots/${currentUser}/timeseries/${currentDistrict}-${currentUser}.png`;
    }
  }

  // 3. Render Top District Navigation Buttons
  const nav = document.getElementById("districtNav");
  if (nav) {
    nav.innerHTML = "";
    districts.forEach(d => {
      const btn = document.createElement("button");
      btn.textContent = d.replace(/_/g, " "); // Display "Ciutat Vella" instead of "Ciutat_Vella"
      
      if (d === currentDistrict) {
        btn.classList.add("active");
      }

      btn.onclick = () => selectDistrict(d);
      nav.appendChild(btn);
    });
  }

  // 4. Render Bottom Thumbnails Grid
  const grid = document.getElementById("districtGrid");
  if (grid) {
    grid.innerHTML = "";
    districts.forEach(d => {
      const img = document.createElement("img");
      img.src = `plots/${currentUser}/${d}-${currentUser}.png`;

      // Visual highlight for the selected district in the grid
      if (d === currentDistrict) {
        img.style.outline = "5px solid #ff4444";
        img.style.outlineOffset = "-5px";
      }

      img.onclick = () => selectDistrict(d);
      grid.appendChild(img);
    });
  }
}

/* Init */
function init() {
  render();
}

/* Events */
window.addEventListener("load", init);
window.addEventListener("hashchange", render);