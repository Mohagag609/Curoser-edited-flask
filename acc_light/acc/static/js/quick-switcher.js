// Quick Project Switcher
class QuickSwitcher {
    constructor() {
        this.isOpen = false;
        this.projects = [];
        this.filteredProjects = [];
        this.selectedIndex = 0;
        this.init();
    }

    init() {
        // إنشاء واجهة Quick Switcher
        this.createModal();
        
        // الاستماع لاختصار لوحة المفاتيح
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                this.toggle();
            }
        });
    }

    createModal() {
        const modal = document.createElement('div');
        modal.id = 'quick-switcher';
        modal.className = 'fixed inset-0 z-50 hidden';
        modal.innerHTML = `
            <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" onclick="quickSwitcher.close()"></div>
            <div class="absolute top-1/4 left-1/2 transform -translate-x-1/2 w-full max-w-2xl">
                <div class="bg-slate-800 rounded-xl shadow-2xl border border-slate-700 overflow-hidden">
                    <div class="p-4 border-b border-slate-700">
                        <input type="text" 
                               id="quick-search" 
                               class="w-full bg-slate-900 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                               placeholder="ابحث عن مشروع... (Ctrl+K)">
                    </div>
                    <div id="quick-results" class="max-h-96 overflow-y-auto">
                        <!-- النتائج ستظهر هنا -->
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // إضافة مستمعي الأحداث
        const searchInput = document.getElementById('quick-search');
        searchInput.addEventListener('input', (e) => this.search(e.target.value));
        searchInput.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }

    async loadProjects() {
        try {
            const response = await fetch('/projects/api/projects');
            this.projects = await response.json();
            this.filteredProjects = this.projects;
            this.render();
        } catch (error) {
            console.error('Error loading projects:', error);
        }
    }

    search(query) {
        if (!query) {
            this.filteredProjects = this.projects;
        } else {
            this.filteredProjects = this.projects.filter(project => 
                project.name.toLowerCase().includes(query.toLowerCase()) ||
                project.code.toLowerCase().includes(query.toLowerCase())
            );
        }
        this.selectedIndex = 0;
        this.render();
    }

    render() {
        const resultsContainer = document.getElementById('quick-results');
        
        if (this.filteredProjects.length === 0) {
            resultsContainer.innerHTML = `
                <div class="p-8 text-center text-gray-400">
                    <i class="fas fa-search text-4xl mb-3"></i>
                    <p>لا توجد نتائج</p>
                </div>
            `;
            return;
        }

        resultsContainer.innerHTML = this.filteredProjects.map((project, index) => `
            <a href="/set-project/${project.id}" 
               class="block px-4 py-3 hover:bg-slate-700 transition-colors ${index === this.selectedIndex ? 'bg-slate-700' : ''}"
               onmouseover="quickSwitcher.selectedIndex = ${index}; quickSwitcher.render();">
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="text-white font-medium">${project.name}</h3>
                        <p class="text-gray-400 text-sm">${project.code} • ${project.project_type}</p>
                    </div>
                    <div class="text-2xl">
                        ${project.project_type === 'عقاري' ? 
                            '<i class="fas fa-building text-green-400"></i>' : 
                            '<i class="fas fa-calculator text-purple-400"></i>'}
                    </div>
                </div>
            </a>
        `).join('');
    }

    handleKeyboard(e) {
        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, this.filteredProjects.length - 1);
                this.render();
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
                this.render();
                break;
            case 'Enter':
                e.preventDefault();
                if (this.filteredProjects[this.selectedIndex]) {
                    window.location.href = `/set-project/${this.filteredProjects[this.selectedIndex].id}`;
                }
                break;
            case 'Escape':
                e.preventDefault();
                this.close();
                break;
        }
    }

    toggle() {
        this.isOpen ? this.close() : this.open();
    }

    open() {
        this.isOpen = true;
        this.loadProjects();
        document.getElementById('quick-switcher').classList.remove('hidden');
        document.getElementById('quick-search').focus();
    }

    close() {
        this.isOpen = false;
        document.getElementById('quick-switcher').classList.add('hidden');
        document.getElementById('quick-search').value = '';
        this.selectedIndex = 0;
    }
}

// تهيئة Quick Switcher
const quickSwitcher = new QuickSwitcher();