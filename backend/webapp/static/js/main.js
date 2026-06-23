/**
 * PaperSplitter — Main JavaScript
 */

// --- Lightbox for question images ---
function openLightbox(imgElement) {
    const lightbox = document.getElementById("lightbox");
    const lightboxImg = document.getElementById("lightbox-img");
    if (!lightbox || !lightboxImg) return;

    lightboxImg.src = imgElement.src;
    lightbox.classList.add("active");
    document.body.style.overflow = "hidden";
}

function closeLightbox() {
    const lightbox = document.getElementById("lightbox");
    if (!lightbox) return;
    lightbox.classList.remove("active");
    document.body.style.overflow = "";
}

// Close lightbox with Escape key
document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
        closeLightbox();
    }
});

// --- Smooth scroll for TOC links ---
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".toc-link").forEach(function (link) {
        link.addEventListener("click", function (e) {
            e.preventDefault();
            const targetId = this.getAttribute("href").slice(1);
            const target = document.getElementById(targetId);
            if (target) {
                const offset = 80; // account for sticky header
                const top = target.getBoundingClientRect().top + window.scrollY - offset;
                window.scrollTo({ top: top, behavior: "smooth" });
            }
        });
    });

    // Highlight active TOC item on scroll (optional enhancement)
    const tocLinks = document.querySelectorAll(".toc-link");
    if (tocLinks.length > 0) {
        const observer = new IntersectionObserver(
            function (entries) {
                entries.forEach(function (entry) {
                    if (entry.isIntersecting) {
                        tocLinks.forEach(function (l) {
                            l.style.background = "";
                        });
                        const activeLink = document.querySelector(
                            '.toc-link[href="#' + entry.target.id + '"]'
                        );
                        if (activeLink) {
                            activeLink.style.background = "#e0e7f0";
                        }
                    }
                });
            },
            { rootMargin: "-80px 0px -60% 0px" }
        );

        document.querySelectorAll(".topic-card[id]").forEach(function (card) {
            observer.observe(card);
        });
    }
});
