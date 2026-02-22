document.addEventListener("DOMContentLoaded", () => {
  const ominexScreen = document.getElementById("ominexScreen");
  const ominexInput  = document.getElementById("ominexInput");
  const ominexSend   = document.getElementById("ominexSend");

  if (!ominexScreen || !ominexInput || !ominexSend) return;

  function addMsg(type, text) {
    const msg = document.createElement("div");
    msg.className = type === "user" ? "ominex-msg user" : "ominex-msg ai";
    msg.textContent = text;
    ominexScreen.appendChild(msg);
    ominexScreen.scrollTop = ominexScreen.scrollHeight;
  }

  function speakText(text) {
    if (!("speechSynthesis" in window)) return;
    speechSynthesis.cancel();
    const speech = new SpeechSynthesisUtterance(text);
    speech.rate = 0.95;
    speech.pitch = 1;
    speech.volume = 1;
    speechSynthesis.speak(speech);
  }

  function typeReply(text) {
    const msg = document.createElement("div");
    msg.className = "ominex-msg ai";
    ominexScreen.appendChild(msg);

    let i = 0;
    const interval = setInterval(() => {
      msg.textContent += text.charAt(i++);
      ominexScreen.scrollTop = ominexScreen.scrollHeight;
      if (i >= text.length) {
        clearInterval(interval);
        speakText(text);
      }
    }, 18);
  }

  // ✅ warm up backend on load (optional but recommended)
  fetch("https://ominex-backend-sxeg.onrender.com/api/ping", { cache: "no-store" })
    .then(() => console.log("✅ OMINEX warmed"))
    .catch(() => console.log("⚠️ warm failed (sleep or network)"));

  typeReply("OMINEX online. Ask me anything.");

  async function sendToOMINEX(message) {
    addMsg("user", message);

    typeReply("Waking up OMINEX… (Render sleep). One moment.");

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 25000);

    try {
      const res = await fetch("https://ominex-backend-sxeg.onrender.com/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
        signal: controller.signal
      });

      const data = await res.json();
      if (data.reply) typeReply(data.reply);
      else typeReply("I got a response, but no reply field returned.");

    } catch (err) {
      console.error("OMINEX API error:", err);
      typeReply("Still waking up. Please try again in 10–20 seconds.");
    } finally {
      clearTimeout(timeout);
    }
  }

  ominexSend.addEventListener("click", () => {
    const msg = ominexInput.value.trim();
    if (!msg) return;
    ominexInput.value = "";
    sendToOMINEX(msg);
  });

  ominexInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      ominexSend.click();
    }
  });
});

document.addEventListener('DOMContentLoaded', function() {
    console.log('%c🎮 GameDesigner Portfolio', 'color: #4ade80; font-size: 24px; font-weight: bold;');
    console.log('%cWelcome to my portfolio! Feel free to explore the code.', 'color: #8b5cf6; font-size: 14px;');

    // Initialize all functionality
    initNavigation();
    initContactForm();
    initShowcase();
    initAnimations();
    initParticles();

    // Navigation functionality
    function initNavigation() {
        const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
        const mobileMenu = document.querySelector('.mobile-menu');
        const navLinks = document.querySelectorAll('a[href^="#"]');
        const sections = document.querySelectorAll('section[id]');
        const navLinksAll = document.querySelectorAll('.nav-link, .mobile-link');

        // Mobile menu toggle
        if (mobileMenuBtn && mobileMenu) {
            mobileMenuBtn.addEventListener('click', function() {
                mobileMenu.classList.toggle('active');
                
                const spans = mobileMenuBtn.querySelectorAll('span');
                if (mobileMenu.classList.contains('active')) {
                    spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                    spans[1].style.opacity = '0';
                    spans[2].style.transform = 'rotate(-45deg) translate(7px, -6px)';
                } else {
                    spans[0].style.transform = 'none';
                    spans[1].style.opacity = '1';
                    spans[2].style.transform = 'none';
                }
            });
        }

        // Smooth scrolling
        navLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                    
                    if (mobileMenu && mobileMenu.classList.contains('active')) {
                        mobileMenu.classList.remove('active');
                        const spans = mobileMenuBtn.querySelectorAll('span');
                        spans[0].style.transform = 'none';
                        spans[1].style.opacity = '1';
                        spans[2].style.transform = 'none';
                    }
                }
            });
        });

        // Update active navigation on scroll
        function updateActiveLink() {
            const scrollPosition = window.scrollY + 100;
            
            sections.forEach(section => {
                const sectionTop = section.offsetTop;
                const sectionHeight = section.offsetHeight;
                const sectionId = section.getAttribute('id');
                
                if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                    navLinksAll.forEach(link => {
                        link.classList.remove('active');
                        if (link.getAttribute('href') === `#${sectionId}`) {
                            link.classList.add('active');
                        }
                    });
                }
            });
        }

        let ticking = false;
        window.addEventListener('scroll', function() {
            if (!ticking) {
                requestAnimationFrame(updateActiveLink);
                ticking = true;
                setTimeout(() => { ticking = false; }, 100);
            }
        });
    }

    // Contact form functionality
    function initContactForm() {
        const contactForm = document.getElementById('contactForm');
        const toast = document.getElementById('toast');
        
        if (!contactForm) return;

        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(contactForm);
            const data = {
                name: formData.get('name'),
                email: formData.get('email'),
                subject: formData.get('subject'),
                message: formData.get('message')
            };

            // Simple validation
            if (!data.name || !data.email || !data.subject || !data.message) {
                showNotification('Please fill in all fields.', 'error');
                return;
            }

            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(data.email)) {
                showNotification('Please enter a valid email address.', 'error');
                return;
            }

            console.log('Form submitted:', data);
            showToast();
            contactForm.reset();
        });

        // Form input animations and validation
        const inputs = document.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });

            input.addEventListener('blur', function() {
                if (!this.value) {
                    this.parentElement.classList.remove('focused');
                }
            });

            input.addEventListener('input', function() {
                validateField(this);
            });
        });

        function validateField(field) {
            const value = field.value.trim();
            let isValid = true;

            field.classList.remove('error');

            switch(field.type) {
                case 'email':
                    isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
                    break;
                case 'text':
                    isValid = value.length >= 2;
                    break;
                default:
                    isValid = value.length > 0;
            }

            if (!isValid && value.length > 0) {
                field.classList.add('error');
            }

            return isValid;
        }

        function showToast() {
            if (!toast) return;
            
            toast.classList.remove('hidden');
            toast.classList.add('show');

            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => {
                    toast.classList.add('hidden');
                }, 300);
            }, 5000);
        }
    }

    // Showcase functionality
    function initShowcase() {
       const showcaseItems = [
                {
                id: 1,
                title: "Star Runner – Solar Challenge",
                category: "Games",
                type: "3D Endless Runner",
                thumbnail: "img/projects/star runner.png",
                description: "High-speed endless runner inspired by Race The Sun. Features dynamic sunset lighting, asteroid waves, boost pads, and progressive difficulty scaling.",
                rating: 4.8,
                downloads: "—",

                playable: true,   // 🔥 THIS WAS MISSING
                demoUrl: "./STAR_RUNNER/index.html", // 🔥 MAKE SURE PATH IS CORRECT

                tech: ["Three.js", "JavaScript", "Procedural Systems", "Game Design"]
            },

           
            {
                id: 99,
                title: "Minecraft World Project",
                category: "Games",
                type: "World Design",
                thumbnail: "img/projects/minecraft.png",
                description: "Custom-designed Minecraft world focused on level design, environmental storytelling, and gameplay flow.",
                rating: 4.6,
                playable: true,
                demoUrl: "./Minecraft/index.html",
                tech: ["Minecraft", "World Design", "Level Design"]
            },


           {
                id: 8,
                title: "Crypto Trade Bot Dashboard",
                category: "UI/UX",
                type: "Web App",
                thumbnail: "img/projects/trade bot.png",
                description: "Interactive trading bot dashboard with real-time indicators, signals, and performance visualization.",
                rating: 4.8,
                downloads: "—",
                tech: ["Python", "Streamlit", "APIs", "Data Visualization"],
                demoUrl: "https://crypto-trade-bot-wdza2prbmz7wnnwrnjrjcm.streamlit.app/"
 // change later to live URL
                },


            {
                id: 7,
                title: "99 Fashion – Lookbook Promo",
                category: "Videos",
                type: "Fashion Promo",
                thumbnail: "img/projects/99 fashion.png",
                description: "High-energy fashion lookbook promo for 99 Fashion featuring bold visuals, dynamic transitions, and Gen-Z inspired styling.",
                rating: 4.9,
                playable: true,
                demoUrl: "./videos/99-lookbook.mp4.mp4",
                tech: ["After Effects", "Video Editing", "Color Grading", "Creative Direction"]
            },

            {
                id: 5,
                title: "Motion Graphics Animation",
                category: "Animations",
                type: "Animation Reel",
                thumbnail: "img/projects/animation reel.png",
                description: "Smooth motion graphics animation designed for visual impact, rhythm, and clean transitions.",
                rating: 4.8,
                downloads: "—",
                tech: ["After Effects", "Motion Design", "Visual Effects"]
            },
            {
                id: 6,
                title: "Experimental Interactive Prototype",
                category: "Games",
                type: "Prototype",
                thumbnail: "img/projects/weather.png",
                description: "Experimental interactive prototype exploring mechanics, visuals, and user feedback in a playable format.",
                rating: 4.7,
                downloads: "—",
                tech: ["Game Prototyping", "Interaction Design", "Creative Coding"]
            }
        ];

        let currentFilter = 'All';
        const showcaseGrid = document.getElementById('showcaseGrid');
        const filterButtons = document.querySelectorAll('.filter-btn');
        const modal = document.getElementById('projectModal');
        const modalClose = document.getElementById('modalClose');
        const modalBody = document.getElementById('modalBody');

        if (!showcaseGrid) return;

        // Render showcase items
        function renderShowcaseItems(items) {
            showcaseGrid.innerHTML = '';
            
            items.forEach((item, index) => {
                const shouldShow = currentFilter === 'All' || item.category === currentFilter;
                
                const itemElement = document.createElement('div');
                itemElement.className = `showcase-item ${!shouldShow ? 'hidden' : ''}`;
                itemElement.style.animationDelay = `${index * 0.1}s`;
                
                itemElement.innerHTML = `
                    <div class="item-thumbnail" 
                        style="background-image: url('${item.thumbnail}');
                                background-size: cover;
                                background-position: center;">

                        <div class="play-overlay"
                            onclick="window.open('${item.demoUrl}', '_blank')">

                            <div class="play-button">
                                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polygon points="5,3 19,12 5,21"></polygon>
                                </svg>
                            </div>
                        </div>
                        
                        <div class="category-badge">${item.type}</div>
                        
                        <div class="rating-badge">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2">
                                <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"></polygon>
                            </svg>
                            <span>${item.rating}</span>
                        </div>
                        
                        <div class="action-buttons">
                            <button class="action-btn" onclick="showNotification('GitHub repository opened!', 'info')">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
                                </svg>
                            </button>
                            <button class="action-btn" onclick="showNotification('External link opened!', 'info')">
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                    <polyline points="15,3 21,3 21,9"></polyline>
                                    <line x1="10" y1="14" x2="21" y2="3"></line>
                                </svg>
                            </button>
                        </div>
                    </div>
                    
                    <div class="item-content">
                        <div class="item-meta">
                            <span class="item-category">${item.category}</span>
                            <span class="item-downloads">${item.downloads || '—'}</span>

                        </div>
                        
                        <h3 class="item-title">${item.title}</h3>
                        
                        <p class="item-description">${item.description}</p>
                        
                        <div class="tech-stack">
                            ${item.tech.map(tech => `<span class="tech-tag">${tech}</span>`).join('')}
                        </div>
                        
                        <div class="item-footer">

    ${item.title === 'Crypto Trade Bot Dashboard' ? `
        <button class="tradebot-btn"
            onclick="window.open('${item.demoUrl}', '_blank')"
            style="
                background: var(--primary);
                color: var(--primary-foreground);
                border: none;
                padding: 10px 16px;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
            ">
            ▶ Open Trade Bot
        </button>
    ` : ''}

    <button class="view-details" onclick="openModal(${item.id})">
        View Details
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
            <polyline points="15,3 21,3 21,9"></polyline>
            <line x1="10" y1="14" x2="21" y2="3"></line>
        </svg>
    </button>

    <div class="item-rating">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2">
            <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"></polygon>
        </svg>
        <span>${item.rating}</span>
    </div>

</div>

                    </div>
                `;
                
                itemElement.addEventListener('click', (e) => {
                    if (
                        !e.target.closest('.action-buttons') &&
                        !e.target.closest('.view-details') &&
                        !e.target.closest('.tradebot-btn')
                    ) {
                        openModal(item.id);
                    }
                });

                
                showcaseGrid.appendChild(itemElement);
            });
        }

        // Filter functionality
        if (filterButtons.length > 0) {
            filterButtons.forEach(button => {
                button.addEventListener('click', () => {
                    filterButtons.forEach(btn => btn.classList.remove('active'));
                    button.classList.add('active');
                    
                    currentFilter = button.dataset.category;
                    filterItems();
                });
            });
        }

        function filterItems() {
            const items = document.querySelectorAll('.showcase-item');
            
            items.forEach((item, index) => {
                const itemData = showcaseItems[index];
                const shouldShow = currentFilter === 'All' || itemData.category === currentFilter;
                
                if (shouldShow) {
                    item.classList.remove('hidden');
                    item.style.animationDelay = `${Array.from(items).filter(i => !i.classList.contains('hidden')).indexOf(item) * 0.1}s`;
                } else {
                    item.classList.add('hidden');
                }
            });
        }

        // Modal functionality
        if (modal && modalClose && modalBody) {
            modalClose.addEventListener('click', closeModal);
            modal.addEventListener('click', (e) => {
                if (e.target === modal || e.target.classList.contains('modal-overlay')) {
                    closeModal();
                }
            });
            
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
                    closeModal();
                }
            });
        }

        function openModal(itemId) {
            const item = showcaseItems.find(i => i.id === itemId);
            if (!item || !item.demoUrl) return;

            window.open(item.demoUrl, "_blank", "noopener,noreferrer");


            
            modalBody.innerHTML = `
                <div style="padding-top: 2rem;">
                    <div style="height: 300px; background: ${item.thumbnail}; border-radius: 8px; margin-bottom: 2rem; display: flex; align-items: center; justify-content: center; position: relative;">
                        <div style="position: absolute; inset: 0; background: rgba(0,0,0,0.3); border-radius: 8px;"></div>
                        <div style="position: relative; z-index: 1; text-align: center;">
                            <div style="width: 80px; height: 80px; background: var(--primary); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem; box-shadow: 0 0 30px rgba(59, 130, 246, 0.5);">
                                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: white; margin-left: 4px;">
                                    <polygon points="5,3 19,12 5,21"></polygon>
                                </svg>
                            </div>
                            <div style="color: white; font-weight: 600;">Interactive Demo Available</div>
                        </div>
                    </div>
                    
                    <div style="padding: 0 2rem 2rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                            <span style="background: var(--primary); color: var(--primary-foreground); padding: 0.5rem 1rem; border-radius: 20px; font-size: 0.875rem;">${item.category}</span>
                            <div style="display: flex; align-items: center; gap: 0.5rem; color: var(--muted-foreground);">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2">
                                    <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"></polygon>
                                </svg>
                                <span>${item.rating}</span>
                                <span style="margin-left: 1rem;">${item.downloads || '—'}</span>

                            </div>
                        </div>
                        
                        <h2 style="font-size: 2rem; font-weight: 700; margin-bottom: 1rem;">${item.title}</h2>
                        
                        <p style="color: var(--muted-foreground); line-height: 1.6; margin-bottom: 1.5rem;">${item.description}</p>
                        
                        <div style="margin-bottom: 1.5rem;">
                            <h3 style="margin-bottom: 0.5rem;">Technologies Used:</h3>
                            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                                ${item.tech.map(tech => `<span style="background: var(--secondary); color: var(--secondary-foreground); padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.875rem; border: 1px solid var(--border);">${tech}</span>`).join('')}
                            </div>
                        </div>
                        
                       <div style="display: flex; gap: 1rem; flex-wrap: wrap;">

                   ${item.playable ? `
                        ${item.category === "Videos" ? `
                            <div style="position:fixed; inset:0; background:black; z-index:99999; display:flex; align-items:center; justify-content:center;">
                                
                                <video id="fullscreenVideo"
                                    controls
                                    autoplay
                                    style="width:100vw; height:100vh; object-fit:contain; background:black;">
                                    <source src="${item.demoUrl}" type="video/mp4">
                                </video>

                                <button onclick="document.getElementById('fullscreenVideo').parentElement.remove()" 
                                    style="position:absolute; top:20px; right:20px; background:rgba(0,0,0,0.6); color:white; border:none; padding:10px 15px; border-radius:8px; font-size:18px; cursor:pointer;">
                                    ✕
                                </button>
                            </div>
                        ` : `
                            ${item.title.includes("Crypto Trade Bot") ? `
                                <button onclick="window.open('${item.demoUrl}', '_blank')" 
                                    style="
                                    background: var(--primary);
                                    color: var(--primary-foreground);
                                    border: none;
                                    padding: 12px 24px;
                                    border-radius: 8px;
                                    font-weight: 600;
                                    cursor: pointer;
                                    ">
                                    ▶ Open Trade Bot
                                </button>
                                ` : ''}


                            <button
                                onclick="window.open('${item.demoUrl}', '_blank')"
                                style="
                                    background: var(--primary);
                                    color: var(--primary-foreground);
                                    border: none;
                                    padding: 12px 24px;
                                    border-radius: 8px;
                                    font-weight: 600;
                                    cursor: pointer;
                                ">
                                ▶ Play Demo
                                </button>

                        `}
                    ` : ''}


                            <button onclick="showNotification('Code repository opened!', 'info')" 
                            style="background: transparent; color: var(--primary); border: 1px solid var(--primary); padding: 12px 24px; border-radius: 8px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 0.5rem;">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
                                </svg>
                                View Code
                            </button>

                        </div>

                        </div>
                    </div>
                </div>
            `;
            
            modal.classList.remove('hidden');
        };

        function closeModal() {
            if (modal) {
                modal.classList.add('hidden');
            }
        }

        // Initialize showcase
        renderShowcaseItems(showcaseItems);
    }

    // Animation functionality
    function initAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);

        // Observe elements for animation
        const animatedElements = document.querySelectorAll('.skill-card, .project-card, .achievement, .contact-item, .collaboration-card, .showcase-item');
        animatedElements.forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(el);
        });

        // Parallax effect
        function updateParallax() {
            const scrolled = window.pageYOffset;
            const heroBackground = document.querySelector('.hero-background');
            if (heroBackground) {
                heroBackground.style.transform = `translateY(${scrolled * 0.5}px)`;
            }
        }

        let parallaxTicking = false;
        window.addEventListener('scroll', function() {
            if (!parallaxTicking) {
                requestAnimationFrame(updateParallax);
                parallaxTicking = true;
                setTimeout(() => { parallaxTicking = false; }, 100);
            }
        });
    }

    // Particles functionality
    function initParticles() {
        function createParticle() {
            const heroSection = document.querySelector('.hero-section');
            if (!heroSection) return;
            
            const particle = document.createElement('div');
            particle.style.cssText = `
                position: absolute;
                width: 2px;
                height: 2px;
                background: var(--primary);
                border-radius: 50%;
                opacity: 0.5;
                pointer-events: none;
                left: ${Math.random() * 100}%;
                top: ${Math.random() * 100}%;
            `;
            
            heroSection.appendChild(particle);
            
            particle.animate([
                { transform: 'translateY(0px)', opacity: 0.5 },
                { transform: 'translateY(-100px)', opacity: 0 }
            ], {
                duration: 3000 + Math.random() * 2000,
                easing: 'ease-out'
            }).addEventListener('finish', () => {
                particle.remove();
            });
        }

        setInterval(createParticle, 500);
    }

    // Global notification function
    window.showNotification = function(message, type = 'info') {
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(notification => notification.remove());
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? 'var(--primary)' : type === 'error' ? '#ef4444' : 'var(--card)'};
            color: ${type === 'success' || type === 'error' ? 'white' : 'var(--foreground)'};
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            animation: slideInRight 0.3s ease;
            max-width: 300px;
            word-wrap: break-word;
            border: 1px solid ${type === 'success' ? 'var(--primary)' : type === 'error' ? '#ef4444' : 'var(--border)'};
        `;
        notification.textContent = message;
        
        if (!document.querySelector('#notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideInRight {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOutRight {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    };

    // Button interactions
    document.addEventListener('click', function(e) {
        // Ripple effect for buttons
        if (e.target.matches('.btn, .filter-btn, .play-button, .submit-btn')) {
            const button = e.target;
            const ripple = document.createElement('span');
            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.height, rect.width);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                pointer-events: none;
                animation: ripple-animation 0.6s ease-out;
            `;
            
            button.style.position = 'relative';
            button.style.overflow = 'hidden';
            button.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 600);
        }

        // Project card button actions
        if (e.target.matches('.project-card .btn')) {
            e.stopPropagation();
            const action = e.target.textContent.trim();
            const projectCard = e.target.closest('.project-card');
            const projectTitle = projectCard.querySelector('.project-title').textContent;
            showNotification(`${action} functionality for "${projectTitle}" would open here.`, 'info');
        }
    });

    // Contact item hover effects
    document.querySelectorAll('.contact-item').forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px) scale(1.02)';
        });

        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });

    // Loading animation
    window.addEventListener('load', function() {
        document.body.style.opacity = '0';
        document.body.style.transition = 'opacity 0.5s ease';
        setTimeout(() => {
            document.body.style.opacity = '1';
        }, 100);
    });



});

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// === OMINEX HYBRID MODE ===


window.addEventListener("load", () => {
  const intro = document.getElementById("gd-intro");
  const sound = document.getElementById("gd-sound");

  if (!intro) return;

  // Play sound gently
  if (sound) {
    sound.volume = 0.8;
    sound.currentTime = 0;
    sound.play().catch(() => {});
  }

  // Remove intro smoothly
  setTimeout(() => {
    intro.style.opacity = "0";
    intro.style.pointerEvents = "none";

    setTimeout(() => intro.remove(), 700);
  }, 2200);
});

const sunCanvas = document.getElementById("sunCanvas");
if (!sunCanvas) {
  console.error("sunCanvas missing");
} else {
  const sunCtx = sunCanvas.getContext("2d");

  function resizeSun() {
    sunCanvas.width = sunCanvas.offsetWidth;
    sunCanvas.height = sunCanvas.offsetHeight;
  }
  window.addEventListener("resize", resizeSun);
  resizeSun();

  let t = 0;

  function drawSun() {
    sunCtx.clearRect(0, 0, sunCanvas.width, sunCanvas.height);

    const cx = sunCanvas.width / 2;
    const cy = sunCanvas.height * 0.65;
    const r = 70 + Math.sin(t * 0.02) * 6;

    const grad = sunCtx.createRadialGradient(cx, cy, 10, cx, cy, r);
    grad.addColorStop(0, "#6ae3ff");
    grad.addColorStop(0.6, "#7c5cff");
    grad.addColorStop(1, "transparent");

    sunCtx.fillStyle = grad;
    sunCtx.beginPath();
    sunCtx.arc(cx, cy, r, 0, Math.PI * 2);
    sunCtx.fill();

    sunCtx.strokeStyle = "rgba(140,200,255,0.25)";
    sunCtx.lineWidth = 2;

    for (let i = -2; i <= 2; i++) {
      sunCtx.beginPath();
      for (let x = 0; x < sunCanvas.width; x++) {
        const y = cy + Math.sin(x * 0.01 + t * 0.03 + i) * 14 + i * 16;
        sunCtx.lineTo(x, y);
      }
      sunCtx.stroke();
    }

    t++;
    requestAnimationFrame(drawSun);
  }

  drawSun();
}

// Project button links (NO DESIGN CHANGE)
document.querySelectorAll(".project-card").forEach(card => {
  const project = card.dataset.project;

  const playBtn = card.querySelector(".btn-primary");
  const codeBtn = card.querySelector(".btn-outline");

  if (project === "game-awaits") {
    playBtn?.addEventListener("click", () => {
      window.open("https://github.com/breezy23333/game-awaits", "_blank");
    });

    codeBtn?.addEventListener("click", () => {
      window.open("https://github.com/breezy23333/game-awaits", "_blank");
    });
  }

  if (project === "cinevault") {
    playBtn?.addEventListener("click", () => {
      window.open("https://cinevault-by-luvo.vercel.app", "_blank");

    });

    codeBtn?.addEventListener("click", () => {
      window.open("https://github.com/breezy23333/cinevault", "_blank");
    });
  }
});

function speak(text) {
  const synth = window.speechSynthesis;
  const utter = new SpeechSynthesisUtterance(text);
  utter.rate = 0.95;
  utter.pitch = 1.05;
  utter.volume = 1;
  synth.speak(utter);
}

document.addEventListener("DOMContentLoaded", () => {
  const bubbles = document.querySelectorAll(".ominex-bubble.ai");

  if (!("speechSynthesis" in window)) return;

  bubbles.forEach((bubble, index) => {
    const text = bubble.innerText.trim();
    bubble.innerText = "";

    let i = 0;
    setTimeout(() => {
      const interval = setInterval(() => {
        bubble.innerText += text.charAt(i);
        i++;
        if (i >= text.length) {
          clearInterval(interval);
          speakOMINEX(text);
        }
      }, 18);
    }, index * 1200);
  });
});

function speakOMINEX(text) {
  const utter = new SpeechSynthesisUtterance(text);
  utter.rate = 0.95;
  utter.pitch = 1;
  utter.volume = 1;
  speechSynthesis.speak(utter);
}
