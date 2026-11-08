(function () {
  'use strict';

  /* ── Configuration ─────────────────────────────────── */
  var GITHUB_USER = 'y-maeda1116';
  var REPOS_API = 'https://api.github.com/users/' + GITHUB_USER + '/repos?sort=updated&per_page=100&type=owner';
  var PAGES_BASE = 'https://' + GITHUB_USER + '.github.io/';
  var EXCLUDED_REPOS = [GITHUB_USER]; // profile README repo

  var TECH_STACK = [
    { name: 'Go',             color: '#00ADD8' },
    { name: 'Python',         color: '#3776AB' },
    { name: 'Linux',          color: '#FCC624' },
    { name: 'AWS',            color: '#FF9900' },
    { name: 'GitHub Actions', color: '#2088FF' },
    { name: 'Docker',         color: '#2496ED' },
    { name: 'Terraform',      color: '#7B42BC' },
    { name: 'CI/CD',          color: '#34d399' },
    { name: 'TypeScript',     color: '#3178C6' },
    { name: 'SRE',            color: '#f472b6' },
  ];

  /* ── Language color map ────────────────────────────── */
  var LANG_COLORS = {
    'Go': '#00ADD8', 'Python': '#3776AB', 'TypeScript': '#3178C6',
    'JavaScript': '#F7DF1E', 'HTML': '#E34F26', 'CSS': '#1572B6',
    'Shell': '#89E051', 'HCL': '#844FBA', 'Dart': '#00B4AB',
    'Ruby': '#CC342D', 'Rust': '#DEA584', 'Java': '#B07219',
    'Astro': '#FF5D01', 'null': '#6b7280',
  };

  /* ── DOM references ────────────────────────────────── */
  var techContainer = document.getElementById('tech-stack');
  var grid = document.getElementById('projects-grid');

  /* ── DOM helper: build element safely ──────────────── */
  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (key) {
        if (key === 'className') {
          node.className = attrs[key];
        } else if (key === 'textContent') {
          node.textContent = attrs[key];
        } else if (key.indexOf('on') === 0) {
          node.addEventListener(key.slice(2).toLowerCase(), attrs[key]);
        } else {
          node.setAttribute(key, attrs[key]);
        }
      });
    }
    if (children) {
      (Array.isArray(children) ? children : [children]).forEach(function (child) {
        if (typeof child === 'string') {
          node.appendChild(document.createTextNode(child));
        } else if (child) {
          node.appendChild(child);
        }
      });
    }
    return node;
  }

  /* ── Render tech stack badges ──────────────────────── */
  function renderTechStack() {
    TECH_STACK.forEach(function (tech) {
      var badge = el('span', {
        className: 'tech-badge inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-surface-3 bg-surface-2 text-sm font-mono text-gray-300 select-none',
      }, [
        el('span', {
          className: 'w-2 h-2 rounded-full',
          'style': 'background-color:' + tech.color,
        }),
        tech.name,
      ]);
      techContainer.appendChild(badge);
    });
  }

  /* ── Create skeleton cards ─────────────────────────── */
  function showSkeletons(count) {
    for (var i = 0; i < count; i++) {
      var card = el('div', {
        className: 'project-card rounded-xl border border-surface-3 bg-surface-1 p-6 flex flex-col gap-4',
      });
      card.appendChild(el('div', { className: 'skeleton h-6 w-3/4' }));
      card.appendChild(el('div', { className: 'skeleton h-4 w-full' }));
      card.appendChild(el('div', { className: 'skeleton h-4 w-2/3' }));
      var footer = el('div', { className: 'mt-auto flex items-center gap-4' });
      footer.appendChild(el('div', { className: 'skeleton h-4 w-16' }));
      footer.appendChild(el('div', { className: 'skeleton h-4 w-20' }));
      card.appendChild(footer);
      grid.appendChild(card);
    }
  }

  /* ── Create error card ─────────────────────────────── */
  function createErrorCard(message) {
    var card = el('div', {
      className: 'rounded-xl border border-red-900/40 bg-surface-1 p-6 flex items-start gap-3',
    });
    var iconWrap = el('div', { className: 'shrink-0 text-red-400 mt-0.5' });
    iconWrap.insertAdjacentHTML('afterbegin',
      '<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
    );
    card.appendChild(iconWrap);
    card.appendChild(el('p', {
      className: 'text-sm text-red-300/80 leading-relaxed',
      textContent: message,
    }));
    return card;
  }

  /* ── Create project card ───────────────────────────── */
  function createProjectCard(repo) {
    var langColor = LANG_COLORS[repo.language] || LANG_COLORS['null'];
    var lang = repo.language || '—';
    var desc = repo.description || 'No description provided';
    var stars = String(repo.stargazers_count);
    var hasPages = repo.has_pages === true;
    var pagesUrl = PAGES_BASE + repo.name + '/';

    var card = el('a', {
      className: 'project-card rounded-xl border border-surface-3 bg-surface-1 p-6 flex flex-col gap-4 no-underline card-focus',
      'href': repo.html_url,
      'target': '_blank',
      'rel': 'noopener noreferrer',
    });

    // Header row: repo name + website link
    var headerRow = el('div', { className: 'flex items-start justify-between gap-2' });
    headerRow.appendChild(el('h3', {
      className: 'font-mono text-base font-semibold text-white card-title transition-colors truncate',
      textContent: repo.name,
    }));
    if (hasPages) {
      var websiteLink = el('a', {
        className: 'shrink-0 inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-mono border border-accent/30 text-accent bg-accent/5 hover:bg-accent/15 transition-colors no-underline',
        'href': pagesUrl,
        'target': '_blank',
        'rel': 'noopener noreferrer',
        'title': 'Open website: ' + pagesUrl,
        'onclick': function (e) { e.stopPropagation(); },
      });
      websiteLink.insertAdjacentHTML('afterbegin',
        '<svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101"/><path stroke-linecap="round" stroke-linejoin="round" d="M10.172 13.828a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.102 1.101"/></svg>'
      );
      websiteLink.appendChild(document.createTextNode('Web'));
      headerRow.appendChild(websiteLink);
    }
    card.appendChild(headerRow);

    // Description
    card.appendChild(el('p', {
      className: 'text-sm text-gray-400 leading-relaxed flex-1 line-clamp-3',
      textContent: desc,
    }));

    // Meta row: language + stars
    var metaRow = el('div', {
      className: 'flex items-center gap-4 mt-auto pt-2 border-t border-surface-3',
    });

    var langBadge = el('span', {
      className: 'inline-flex items-center gap-1.5 text-xs text-gray-500 font-mono',
    }, [
      el('span', {
        className: 'w-2.5 h-2.5 rounded-full',
        'style': 'background-color:' + langColor,
      }),
      lang,
    ]);
    metaRow.appendChild(langBadge);

    var starBadge = el('span', {
      className: 'inline-flex items-center gap-1 text-xs text-gray-500 font-mono star-icon',
    });
    starBadge.insertAdjacentHTML('afterbegin',
      '<svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87L18.18 22 12 18.56 5.82 22 7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>'
    );
    starBadge.appendChild(document.createTextNode(stars));
    metaRow.appendChild(starBadge);

    card.appendChild(metaRow);
    return card;
  }

  /* ── Filter repos ──────────────────────────────────── */
  function filterRepos(repos) {
    return repos.filter(function (repo) {
      if (repo.fork) return false;
      if (EXCLUDED_REPOS.indexOf(repo.name) !== -1) return false;
      return true;
    });
  }

  /* ── Fetch all repos (with pagination) ─────────────── */
  function fetchAllRepos(url) {
    return fetch(url, {
      headers: { 'Accept': 'application/vnd.github.v3+json' },
    }).then(function (res) {
      if (!res.ok) {
        throw new Error('GitHub API error: HTTP ' + res.status + ' ' + res.statusText);
      }
      return res.json().then(function (data) {
        // Check for next page via Link header
        var linkHeader = res.headers.get('Link') || '';
        var nextMatch = linkHeader.match(/<([^>]+)>;\s*rel="next"/);
        if (nextMatch) {
          return fetchAllRepos(nextMatch[1]).then(function (nextData) {
            return data.concat(nextData);
          });
        }
        return data;
      });
    });
  }

  /* ── Load and render projects ──────────────────────── */
  function loadProjects() {
    // Show skeleton placeholders while loading
    showSkeletons(6);

    fetchAllRepos(REPOS_API)
      .then(function (repos) {
        var filtered = filterRepos(repos);

        // Clear skeletons
        grid.textContent = '';

        if (filtered.length === 0) {
          grid.appendChild(createErrorCard('No repositories found.'));
          return;
        }

        filtered.forEach(function (repo) {
          grid.appendChild(createProjectCard(repo));
        });
      })
      .catch(function (err) {
        grid.textContent = '';
        grid.appendChild(createErrorCard(
          'Failed to load repositories: ' + err.message
        ));
      });
  }

  /* ── Initialize ────────────────────────────────────── */
  renderTechStack();
  loadProjects();
})();
