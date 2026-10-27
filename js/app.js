/* ==========================================================================
   sllt — Minimalist Developer Blog Runtime (app.js)
   Theme sync, Syntax Highlighting, Margin TOC Scroll-Spy, Code Copy & Tag Filtering
   ========================================================================== */

(function () {
  const saved = localStorage.getItem('blog_theme') || 'light';
  document.documentElement.setAttribute('data-theme', saved);

  const sunIcon =
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>';
  const moonIcon =
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('blog_theme', theme);
    document.querySelectorAll('[data-action="theme"]').forEach((btn) => {
      btn.innerHTML = theme === 'dark' ? sunIcon : moonIcon;
      btn.setAttribute('title', theme === 'dark' ? 'Switch to Light' : 'Switch to Dark');
    });
  }

  function toggleTheme() {
    const cur = document.documentElement.getAttribute('data-theme') || 'light';
    const next = cur === 'dark' ? 'light' : 'dark';
    setTheme(next);
    if (window.parent && window.parent !== window) {
      window.parent.postMessage({ type: 'THEME_CHANGED', theme: next }, '*');
    }
  }

  window.addEventListener('message', (e) => {
    if (e.data && e.data.type === 'SET_THEME') {
      setTheme(e.data.theme);
    }
  });

  /* ------------------------------------------------------------------------
     Lightweight Line-by-Line Syntax Highlighter for .code-block
     Emits: .tok-kw, .tok-fn, .tok-str, .tok-num, .tok-cmt, .tok-typ
     ------------------------------------------------------------------------ */
  function escHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  const DQ = /"(?:[^"\\\n]|\\.)*"/.source;
  const SQ = /'(?:[^'\\\n]|\\.)*'/.source;
  const NUM = /\b0[xX][0-9a-fA-F_]+\b|\b0[bB][01_]+\b|\b\d[\d_]*(?:\.\d+)?(?:[eE][+-]?\d+)?\b/.source;
  const CALL = /[A-Za-z_]\w*(?=\s*\()/.source;
  const TYPE_ID = /\b[A-Z][A-Za-z0-9_]*\b/.source;
  const KW = (w) => '\\b(?:' + w + ')\\b';

  const LANGS = {
    python: [
      ['cmt', /#[^\n]*/.source],
      ['str', /(?:[rRbBfFuU]{0,2})(?:"(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*')/.source],
      ['kw', KW('and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield')],
      ['num', KW('True|False|None') + '|' + NUM],
      ['fn', /@[\w.]+/.source + '|' + CALL],
      ['typ', TYPE_ID],
    ],
    scheme: [
      ['cmt', /;[^\n]*/.source],
      ['str', DQ],
      ['kw', /(?<=[( ])(?:define|lambda|if|cond|else|let|begin|quote|set!|and|or)(?=[ )\n]|$)/.source],
      ['num', /#[tf]\b/.source + '|' + NUM],
      ['fn', /(?<=\()[^()\s]+/.source],
    ],
    http: [
      ['kw', /^(?:GET|POST|PUT|DELETE|HEAD|OPTIONS|PATCH|HTTP\/1\.[01])\b/.source],
      ['fn', /^[A-Za-z0-9-]+(?=:)/.source],
      ['num', NUM],
      ['str', DQ],
    ],
    go: [
      ['cmt', /\/\/[^\n]*/.source],
      ['str', DQ + '|' + SQ + '|`[^`]*`'],
      ['kw', KW('break|case|chan|const|continue|default|defer|else|fallthrough|for|func|go|goto|if|import|interface|map|package|range|return|select|struct|switch|type|var')],
      ['num', KW('nil|true|false|iota') + '|' + NUM],
      ['fn', CALL],
      ['typ', KW('int|int64|uint64|string|bool|byte|error|float64') + '|' + TYPE_ID],
    ],
    ruby: [
      ['cmt', /#[^\n]*/.source],
      ['str', DQ + '|' + SQ],
      ['kw', KW('def|class|module|end|if|elsif|else|unless|while|until|for|in|do|return|yield|self|super|nil|true|false|require|include|extend|attr_accessor|attr_reader|attr_writer|begin|rescue|ensure|raise')],
      ['num', /:[A-Za-z_]\w*/.source + '|' + NUM],
      ['fn', CALL],
      ['typ', TYPE_ID],
    ],
    nim: [
      ['cmt', /#[^\n]*/.source],
      ['str', DQ],
      ['kw', KW('var|let|const|proc|func|method|iterator|macro|template|type|object|enum|if|elif|else|case|of|when|while|for|in|break|continue|return|yield|import|from|export|try|except|finally|raise|nil|true|false|and|or|not|xor|shl|shr|div|mod')],
      ['num', NUM],
      ['fn', CALL],
      ['typ', TYPE_ID],
    ],
    bash: [
      ['cmt', /#[^\n]*/.source],
      ['str', DQ + '|' + SQ],
      ['kw', KW('if|then|else|elif|fi|for|while|until|do|done|case|esac|function|in|echo|printf|export|local|return|exit|cd|mkdir|curl|python3|python|bundle|gem')],
      ['num', /\$\{[^}\n]*\}|\$[\w?#@!*]+/.source + '|' + NUM],
      ['fn', CALL],
    ],
    clike: [
      ['cmt', /\/\/[^\n]*/.source],
      ['str', DQ + '|' + SQ],
      ['kw', KW('abstract|async|await|break|case|catch|class|const|constexpr|continue|default|delete|do|else|enum|explicit|export|extends|extern|final|finally|fn|for|from|function|goto|if|impl|implements|import|in|inline|instanceof|interface|let|loop|match|mod|move|mut|namespace|new|override|package|private|protected|pub|public|ref|return|self|static|struct|super|switch|template|this|throw|throws|trait|try|type|typedef|typename|typeof|union|unsafe|use|using|var|virtual|void|volatile|where|while|yield')],
      ['num', KW('true|false|null|nullptr|undefined') + '|' + NUM],
      ['fn', CALL],
      ['typ', TYPE_ID],
    ],
  };

  const ALIAS = {
    py: 'python',
    scm: 'scheme',
    lisp: 'scheme',
    golang: 'go',
    rb: 'ruby',
    sh: 'bash',
    shell: 'bash',
    zsh: 'bash',
    console: 'bash',
    js: 'clike',
    javascript: 'clike',
    ts: 'clike',
    typescript: 'clike',
    java: 'clike',
    c: 'clike',
    cpp: 'clike',
    'c++': 'clike',
    cuda: 'clike',
    rs: 'clike',
    rust: 'clike',
  };

  function compileLang(rules) {
    const src = rules.map(([cls, pat]) => `(?<${cls}>${pat})`).join('|');
    return new RegExp(src, 'g');
  }

  const COMPILED = {};

  function highlightLine(text, lang) {
    if (!COMPILED[lang]) {
      COMPILED[lang] = compileLang(LANGS[lang]);
    }
    const regex = COMPILED[lang];
    regex.lastIndex = 0;
    let out = '';
    let last = 0;
    let m;
    while ((m = regex.exec(text)) !== null) {
      out += escHtml(text.slice(last, m.index));
      let cls = '';
      if (m.groups) {
        for (const k of ['cmt', 'str', 'kw', 'num', 'fn', 'typ']) {
          if (m.groups[k] !== undefined) {
            cls = 'tok-' + k;
            break;
          }
        }
      }
      out += cls ? `<span class="${cls}">${escHtml(m[0])}</span>` : escHtml(m[0]);
      last = m.index + m[0].length;
      if (m[0] === '') regex.lastIndex++;
    }
    return out + escHtml(text.slice(last));
  }

  function highlightCodeBlocks() {
    document.querySelectorAll('.code-block[data-lang]').forEach((block) => {
      let lang = (block.getAttribute('data-lang') || '').toLowerCase();
      lang = ALIAS[lang] || lang;
      const lines = block.querySelectorAll('.code-line');

      if (lang === 'diff') {
        lines.forEach((lineEl) => {
          const lc = lineEl.querySelector('.lc');
          if (!lc) return;
          const raw = lc.textContent || '';
          if (raw.startsWith('+')) lineEl.classList.add('add');
          else if (raw.startsWith('-')) lineEl.classList.add('del');
        });
        return;
      }

      if (!LANGS[lang]) return;

      lines.forEach((lineEl) => {
        const lc = lineEl.querySelector('.lc');
        if (!lc || lc.querySelector('[class^="tok-"]')) return;
        lc.innerHTML = highlightLine(lc.textContent || '', lang);
      });
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    setTheme(document.documentElement.getAttribute('data-theme') || 'light');

    document.querySelectorAll('[data-action="theme"]').forEach((btn) => {
      btn.addEventListener('click', toggleTheme);
    });

    highlightCodeBlocks();

    // Copy Code
    document.querySelectorAll('.copy-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const block = btn.closest('.code-block');
        if (!block) return;
        const text = Array.from(block.querySelectorAll('.lc'))
          .map((el) => el.textContent)
          .join('\n');
        navigator.clipboard?.writeText(text).catch(() => {});
        const label = btn.querySelector('.copy-label');
        if (label) {
          label.textContent = 'Copied';
        } else {
          btn.textContent = '✓ Copied';
        }
        btn.classList.add('copied');
        setTimeout(() => {
          if (label) {
            label.textContent = 'Copy';
          } else {
            btn.textContent = 'Copy';
          }
          btn.classList.remove('copied');
        }, 1500);
      });
    });

    // Margin TOC Scroll-Spy (supports h2 & h3)
    const headings = Array.from(document.querySelectorAll('.prose h2[id], .prose h3[id]'));
    const tocLinks = Array.from(document.querySelectorAll('.margin-toc a'));
    if (headings.length && tocLinks.length) {
      function onScroll() {
        let activeId = headings[0].id;
        for (const h of headings) {
          if (h.getBoundingClientRect().top <= 130) {
            activeId = h.id;
          }
        }
        tocLinks.forEach((a) => {
          const href = decodeURIComponent(a.getAttribute('href') || '');
          const isActive = href === '#' + activeId;
          a.classList.toggle('active', isActive);
        });
      }
      window.addEventListener('scroll', onScroll, { passive: true });
      onScroll();
    }

    // Tag Filter on /tags/ (archive.html)
    const filters = document.querySelectorAll('[data-filter]');
    const items = document.querySelectorAll('[data-tags]');
    if (filters.length && items.length) {
      function applyTagFilter(tag) {
        let matchedBtn = null;
        filters.forEach((b) => {
          const isMatch = b.getAttribute('data-filter') === tag;
          b.classList.toggle('active', isMatch);
          if (isMatch) matchedBtn = b;
        });
        if (!matchedBtn) {
          tag = 'all';
          filters[0].classList.add('active');
        }
        items.forEach((el) => {
          const tags = (el.getAttribute('data-tags') || '').split(',');
          el.style.display = tag === 'all' || tags.includes(tag) ? '' : 'none';
        });
      }

      filters.forEach((btn) => {
        btn.addEventListener('click', () => {
          const tag = btn.getAttribute('data-filter');
          applyTagFilter(tag);
          if (tag === 'all') {
            history.replaceState(null, '', window.location.pathname);
          } else {
            history.replaceState(null, '', '#' + encodeURIComponent(tag));
          }
        });
      });

      const initialHash = decodeURIComponent(window.location.hash.replace(/^#/, ''));
      if (initialHash) {
        applyTagFilter(initialHash);
      }
      window.addEventListener('hashchange', () => {
        const hashTag = decodeURIComponent(window.location.hash.replace(/^#/, '')) || 'all';
        applyTagFilter(hashTag);
      });
    }
  });
})();
