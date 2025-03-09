document.addEventListener("DOMContentLoaded", function () {
    // Function to animate numbers on hover
    function animateNumberOnHover(element) {
        let originalValue = parseInt(element.getAttribute("data-value")); // Get actual number
        let animated = false; // Prevent re-animation if already done
        
        element.addEventListener("mouseenter", function () {
            if (!animated) {
                gsap.to(element, {
                    textContent: originalValue,
                    duration: 1.5,
                    roundProps: "textContent",
                    ease: "power1.out",
                });
                animated = true;
            }
        });

        element.addEventListener("mouseleave", function () {
            gsap.to(element, {
                textContent: 0,
                duration: 1,
                roundProps: "textContent",
                ease: "power1.inOut",
            });
            animated = false;
        });
    }

    // Select all number elements
    document.querySelectorAll(".animated-number").forEach(animateNumberOnHover);
});
