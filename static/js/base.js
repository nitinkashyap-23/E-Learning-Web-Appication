
const searchInput =
document.getElementById("searchInput");

const searchResults =
document.getElementById("searchResults");
searchInput.addEventListener("keyup", () => {
    let query = searchInput.value;

    if(query.length < 1){

        searchResults.style.display = "none";

        return;
    }
    fetch(`/search-courses/?query=${query}`)
    .then(response => response.json())
    .then(data => {
        searchResults.innerHTML = "";
        if(data.length > 0){
            searchResults.style.display = "block";
            data.forEach(course => {
                searchResults.innerHTML += `
                    <div class="search-item"
                         onclick="window.location.href='/course/${course.slug}/'">
                        ${course.title}
                    </div>
                `;
            });

        }

        else{

            searchResults.style.display = "block";

            searchResults.innerHTML = `

                <div class="search-item">

                    Course Not Found

                </div>

            `;
        }

    });

});


document.addEventListener("click", (e) => {

    if(!document.querySelector(".nav-search")
        .contains(e.target)){

        searchResults.style.display = "none";
    }

});

const menuToggle = document.getElementById("menuToggle");
const navLinks = document.querySelector(".nav-links");

if(menuToggle){
    menuToggle.addEventListener("click", () => {
        navLinks.classList.toggle("active");
    });
}


const toggleBtn =
document.getElementById("toggleTestimonialBtn");

const testimonialForm =
document.getElementById("testimonialForm");

if(toggleBtn){

    toggleBtn.addEventListener("click", () => {

        testimonialForm.classList.toggle("active");

    });

}