const districts = ["Barcelona", "Ciutat_Vella", "Eixample", "Sants_Montjuic", "Les_Corts", "Sarria_Sant_Gervasi", "Gracia", "Horta_Guinardo", "Nou_Barris", "Sant_Andreu", "Sant_Marti"]

const defaultUser = "PA";
const defaultDistrict = "Barcelona";

let currentUser = defaultUser;
let currentDistrict = defaultDistrict;

/* Navigate user */
function navigate(user) {
  updateURL(user, currentDistrict);
}

/* Select district */
function selectDistrict(district) {
  updateURL(currentUser, district);
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

/* Render images */
function render() {
    readURL(); // Ensure we have the latest user/district before rendering
  
    // Use optional chaining or an if-check to prevent "null" errors
    // const barElem = document.getElementById("bar");
    // if (barElem) {
    //   barElem.src = `plots/${currentUser}/bar.jpg`;
    // }
  
    const mainPicElem = document.getElementById("main_pic");
    mainPicElem.src = `plots/${currentUser}/${currentDistrict}-${currentUser}.png`;

  
    const tableStatsElem = document.getElementById("table_stats");
    tableStatsElem.src = `stats/${currentUser}/stats-${currentDistrict}-${currentUser}.png`;
  
    const timeseriesElem = document.getElementById("timeseries");
    timeseriesElem.src = `plots/${currentUser}/timeseries/${currentDistrict}-${currentUser}.png`;
  
  const grid = document.getElementById("districtGrid");
  grid.innerHTML = "";

  districts.forEach(d => {
    const img = document.createElement("img");
    img.src = `plots/${currentUser}/${d}-${currentUser}.png`;

    if (d === currentDistrict) {
      img.style.outline = "3px solid red"; // highlight selected
    }

    img.onclick = () => selectDistrict(d);
    grid.appendChild(img);
  });
}

/* Init */
function init() {
  readURL();
  render();
}

/* Events */
window.addEventListener("load", init);
window.addEventListener("hashchange", init);
