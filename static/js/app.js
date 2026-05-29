const { createApp, ref, computed, watch, onMounted, onUnmounted, nextTick } = Vue;
createApp({
    setup() {
        const API = '';
        const newsList = ref([]);
        const topNews = ref([]);
        const stats = ref({total:0,scored:0,today:0,last_update:null});
        const sortType = ref('latest');
        const filterSource = ref('all');
        const dateFilter = ref('all');
        const searchText = ref('');
        const loading = ref(true);
        const showSettings = ref(false);
        const settingsTab = ref('刷新设置');
        const weights = ref({政治:10,经济:15,科技:20,军事:5,社会:5,文化:5,突发:10,财经:15});
        const blockedKeywords = ref([]);
        const newKeyword = ref('');
        const aiModel = ref('mimo-v2.5');
        const toast = ref(null);

        // 实时更新
        const refreshInterval = ref(30);
        const collectInterval = ref(180);
        const showBreakingBanner = ref(true);
        const breakingThreshold = ref(85);
        const breakingTypes = ref(['all']);
        const showNewNotif = ref(true);
        const breakingNews = ref(null);

        // 精细筛选
        const filterDirection = ref('all');
        const filterAuthor = ref('all');
        const authorOptions = ref([]);
        const showAuthorPicker = ref(false);
        const authorListRef = ref(null);

        // 按首字母分组的作者列表
        const groupedAuthors = computed(() => {
            const groups = {};
            const sorted = [...authorOptions.value].sort((a, b) => {
                const la = (a[0] || '').toUpperCase();
                const lb = (b[0] || '').toUpperCase();
                // 中文按拼音首字母分组简化：非ASCII统一归到#类
                const isAsciiA = la.charCodeAt(0) >= 65 && la.charCodeAt(0) <= 90;
                const isAsciiB = lb.charCodeAt(0) >= 65 && lb.charCodeAt(0) <= 90;
                if (isAsciiA && isAsciiB) return la.localeCompare(lb);
                if (isAsciiA) return -1;
                if (isAsciiB) return 1;
                return a.localeCompare(b, 'zh');
            });
            sorted.forEach(name => {
                const ch = (name[0] || '').toUpperCase();
                const letter = (ch.charCodeAt(0) >= 65 && ch.charCodeAt(0) <= 90) ? ch : '#';
                if (!groups[letter]) groups[letter] = [];
                groups[letter].push(name);
            });
            return groups;
        });
        const authorLetters = computed(() => Object.keys(groupedAuthors.value));
        const scrollToLetter = (letter) => {
            const el = document.getElementById('letter-' + letter);
            if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        };

        // AI总结方向
        const summaryFocus = ref('');
        const updateToast = ref(null);
        const showUpdatePanel = ref(false);
        const updateList = ref([]);
        const knownIds = ref(new Set());

        const summaryModal = ref(null);
        const chatMessages = ref([]);
        const chatInput = ref('');
        const chatLoading = ref(false);
        const chatBox = ref(null);

        const showRAGChat = ref(false);
        const ragMessages = ref([]);
        const ragInput = ref('');
        const ragLoading = ref(false);
        const ragChatBox = ref(null);

        const batchLoading = ref(false);
        const batchProgress = ref('');

        // AI分析功能
        const analysisTab = ref('');
        const analysisData = ref(null);
        const analysisLoading = ref(false);
        const showMarketBrief = ref(false);
        const marketBriefText = ref('');
        const marketBriefLoading = ref(false);

        let pollTimer = null;
        let collectTimer = null;
        const _timeouts = [];  // 跟踪所有setTimeout以便清理

        const sourceOptions = [
            {label:'全部', value:'all', color:null},
            {label:'媒体', value:'media', color:'#3b82f6'},
            {label:'X', value:'x', color:'#8b5cf6'},
            {label:'热搜', value:'hotlist', color:'#ef4444'},
            {label:'科技', value:'tech', color:'#06b6d4'},
            {label:'财经', value:'finance', color:'#f59e0b'},
            {label:'央行', value:'fed', color:'#f97316'},
            {label:'外交', value:'diplomatic', color:'#10b981'},
            {label:'学术', value:'science', color:'#8b5cf6'},
            {label:'加密', value:'crypto', color:'#f59e0b'},
            {label:'地缘', value:'geopolitical', color:'#ef4444'},
        ];
        const dateOptions = [
            {label:'今天', value:'0'},
            {label:'近3天', value:'3'},
            {label:'近7天', value:'7'},
            {label:'全部', value:'all'},
        ];
        const directionOptions = [
            {label:'全部方向', value:'all'},
            {label:'政治', value:'政治'},
            {label:'经济', value:'经济'},
            {label:'科技', value:'科技'},
            {label:'军事', value:'军事'},
            {label:'社会', value:'社会'},
            {label:'文化', value:'文化'},
            {label:'突发', value:'突发'},
            {label:'财经', value:'财经'},
        ];
        const focusOptions = ['通用','经济','科技','政治','军事','社会','文化','突发','财经'];
        const breakingTypeOptions = sourceOptions.filter(s => s.value !== 'all');

        const showToast = (msg, type='ok') => { toast.value={msg,type}; setTimeout(()=>toast.value=null,2500); };
        const getScoreLevel = (s) => {
            if(s===null||s===undefined) return 'E';
            if(s>=95) return 'Splus'; if(s>=85) return 'S'; if(s>=70) return 'A';
            if(s>=50) return 'B'; if(s>=30) return 'C'; if(s>=15) return 'D'; return 'E';
        };
        const getScoreColor = (s) => {
            if(s===undefined||s===null) return '#3b3f54';
            if(s>=95) return '#dc2626'; if(s>=85) return '#f97316'; if(s>=70) return '#eab308';
            if(s>=50) return '#22c55e'; if(s>=30) return '#3b82f6'; return '#3b3f54';
        };
        const truncate = (s, n) => s && s.length > n ? s.slice(0, n) + '..' : s;
        const getSourceTagClass = (type) => ({
            media:'bg-blue-500/10 text-blue-400', x:'bg-purple-500/10 text-purple-400',
            hotlist:'bg-red-500/10 text-red-400', tech:'bg-cyan-500/10 text-cyan-400',
            finance:'bg-amber-500/10 text-amber-400', fed:'bg-orange-500/10 text-orange-400',
            diplomatic:'bg-emerald-500/10 text-emerald-400', science:'bg-violet-500/10 text-violet-400',
            crypto:'bg-amber-500/10 text-amber-400', geopolitical:'bg-red-500/10 text-red-400',
        }[type] || 'bg-dark-4 text-gray-400');

        const parseTime = (dt) => {
            if(!dt) return null;
            return new Date(dt.replace(' ','T'));
        };
        const timeAgo = (dt) => {
            const d = parseTime(dt);
            if(!d) return '';
            const now = new Date();
            const diff = Math.floor((now - d) / 1000);
            if(diff<0) return '刚刚'; if(diff<60) return '刚刚';
            if(diff<3600) return Math.floor(diff/60)+'分钟前';
            if(diff<86400) return Math.floor(diff/3600)+'小时前';
            if(diff<604800) return Math.floor(diff/86400)+'天前';
            return d.toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false});
        };
        const formatPubTime = (dt) => {
            const d = parseTime(dt);
            if(!d) return '';
            const now = new Date();
            const diff = Math.floor((now - d) / 1000);
            if(diff >= 0 && diff < 86400) {
                if(diff<60) return '刚刚';
                if(diff<3600) return Math.floor(diff/60)+'分钟前';
                return Math.floor(diff/3600)+'小时前';
            }
            const isToday = d.toDateString() === now.toDateString();
            if(isToday) return d.toLocaleString('zh-CN',{hour:'2-digit',minute:'2-digit',hour12:false});
            const yesterday = new Date(now); yesterday.setDate(now.getDate()-1);
            if(d.toDateString() === yesterday.toDateString()) return '昨天 '+d.toLocaleString('zh-CN',{hour:'2-digit',minute:'2-digit',hour12:false});
            return d.toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hour12:false});
        };
        const formatLocalTime = (dt) => {
            const d = parseTime(dt);
            if(!d) return '';
            return d.toLocaleString('zh-CN',{hour12:false,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'});
        };
        const formatSummary = (text) => {
            if(!text) return '';
            let html = text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/^### (.*?)$/gm, '<div style="font-size:13px;font-weight:600;margin:8px 0 4px;color:#f3f4f6">$1</div>')
                .replace(/^- (.*?)$/gm, '<div style="padding-left:10px">• $1</div>')
                .replace(/^(\d+)\. (.*?)$/gm, '<div style="padding-left:10px">$1. $2</div>')
                .replace(/\n/g, '<br>');
            return DOMPurify.sanitize(html, {
                ALLOWED_TAGS: ['strong', 'br', 'div', 'span'],
                ALLOWED_ATTR: ['style']
            });
        };

        const topNewsIds = ref(new Set());
        let _loadNewsVersion = 0;  // 防止并发竞态

        // 单独加载AI精选（始终按分数排序，不受当前排序影响）
        const loadTopNews = async () => {
            try {
                const p = new URLSearchParams({sort:'score', source:'all', limit:'500'});
                const data = await (await fetch(`${API}/api/news?${p}`)).json();
                topNews.value = data.filter(n=>n.ai_score&&n.ai_score>=85);
                topNewsIds.value = new Set(topNews.value.map(n => n.id));
            } catch(e) { console.error(e); }
        };

        // 带新内容检测的加载
        const loadNews = async (detectNew = false) => {
            const version = ++_loadNewsVersion;
            try {
                const p = new URLSearchParams({sort:sortType.value, source:filterSource.value, limit:'500'});
                if(dateFilter.value !== 'all') p.set('days', dateFilter.value);
                if(searchText.value) p.set('keyword', searchText.value);
                if(filterDirection.value !== 'all') p.set('direction', filterDirection.value);
                if(filterAuthor.value !== 'all') p.set('author', filterAuthor.value);
                const data = await (await fetch(`${API}/api/news?${p}`)).json();
                if(version !== _loadNewsVersion) return;  // 有更新的请求，丢弃旧数据

                if(detectNew && knownIds.value.size > 0) {
                    const newItems = data.filter(n => !knownIds.value.has(n.id));
                    if(newItems.length > 0) {
                        newItems.forEach(n => n._isNew = true);
                        updateList.value = [...newItems, ...updateList.value].slice(0, 50);

                        if(showNewNotif.value) {
                            updateToast.value = {count: newItems.length};
                            setTimeout(() => { updateToast.value = null; }, 5000);
                        }

                        if(showBreakingBanner.value) {
                            const types = breakingTypes.value;
                            const important = newItems.find(n => n.ai_score && n.ai_score >= breakingThreshold.value &&
                                (types.includes('all') || types.includes(n.source_type)));
                            if(important) {
                                breakingNews.value = important;
                                _timeouts.push(setTimeout(() => { breakingNews.value = null; }, 15000));
                            }
                        }
                    }
                    _timeouts.push(setTimeout(() => {
                        newsList.value.forEach(n => n._isNew = false);
                    }, 5000));
                }

                newsList.value = data;
                if(topNews.value.length === 0) loadTopNews();
                knownIds.value = new Set(data.map(n => n.id));
            } catch(e) { console.error(e); }
            loading.value = false;
        };

        const loadStats = async () => { try { stats.value = await (await fetch(`${API}/api/statistics`)).json(); } catch(e) {} };
        const doSearch = () => loadNews();
        const filteredNews = computed(() => {
            let list = newsList.value;
            // 排除已在AI精选中显示的项目
            if(topNewsIds.value.size > 0) {
                list = list.filter(n => !topNewsIds.value.has(n.id));
            }
            // 后端已过滤source_type和blockedKeywords，前端仅处理客户端新增的屏蔽词
            return list;
        });

        const openSummary = async (news) => {
            summaryModal.value = {id:news.id, title:news.title, link:news.link, loading:true, text:null, error:null, cached:false};
            chatMessages.value = []; chatInput.value = ''; summaryFocus.value = '';
            try {
                const r = await fetch(`${API}/api/news/${news.id}/summary`);
                const data = await r.json();
                if(data.error) { summaryModal.value.error = data.error; }
                else { summaryModal.value.text = data.summary; summaryModal.value.cached = data.cached; if(!data.cached) showToast('✅ '+truncate(news.title,20)+' 总结完成'); }
            } catch(e) { summaryModal.value.error = '请求失败'; }
            summaryModal.value.loading = false;
        };

        const regenerateSummary = async () => {
            if(!summaryModal.value) return;
            const id = summaryModal.value.id;
            summaryModal.value.loading = true; summaryModal.value.text = null; summaryModal.value.error = null;
            try {
                const p = new URLSearchParams();
                if(summaryFocus.value) p.set('focus', summaryFocus.value);
                p.set('regenerate', '1');
                const r = await fetch(`${API}/api/news/${id}/summary?${p}`);
                const data = await r.json();
                if(data.error) { summaryModal.value.error = data.error; }
                else { summaryModal.value.text = data.summary; summaryModal.value.cached = false; showToast('✅ 重新生成完成'); }
            } catch(e) { summaryModal.value.error = '请求失败'; }
            summaryModal.value.loading = false;
        };

        const loadAnalysis = async (newsId, tab) => {
            analysisTab.value = tab;
            analysisData.value = null;
            analysisLoading.value = true;
            const endpoint = tab === '风险评估' ? 'risk' : tab === '影响预测' ? 'impact' : 'perspectives';
            try {
                const r = await fetch(`${API}/api/news/${newsId}/${endpoint}`);
                const data = await r.json();
                if(data.error) { showToast(data.error, 'err'); }
                else { analysisData.value = data; }
            } catch(e) { showToast('分析失败', 'err'); }
            analysisLoading.value = false;
        };

        const openMarketBrief = async () => {
            showMarketBrief.value = true;
            marketBriefLoading.value = true;
            marketBriefText.value = '';
            try {
                const r = await fetch(`${API}/api/market/brief?stream=0`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:'生成今日市场简报'})});
                const data = await r.json();
                if(data.error) { marketBriefText.value = 'AI服务暂时繁忙，请稍后再试'; }
                else { marketBriefText.value = data.text || '暂无足够财经数据生成简报'; }
            } catch(e) { marketBriefText.value = '请求失败，请检查网络后重试'; console.error('市场简报错误:', e); }
            marketBriefLoading.value = false;
        };

        const toggleBookmark = async (newsId) => {
            try {
                const r = await fetch(`${API}/api/news/${newsId}/bookmark`, {method:'POST'});
                const data = await r.json();
                if(data.status === 'ok') {
                    const item = newsList.value.find(n => n.id === newsId);
                    if(item) item.is_bookmarked = data.is_bookmarked;
                    showToast(data.is_bookmarked ? '已收藏' : '已取消收藏');
                }
            } catch(e) { showToast('操作失败', 'err'); }
        };

        const sendChat = async () => {
            if(!chatInput.value.trim()||chatLoading.value||!summaryModal.value) return;
            const msg = chatInput.value.trim(); chatMessages.value.push({role:'user',text:msg}); chatInput.value = ''; chatLoading.value = true;
            await nextTick(); if(chatBox.value) chatBox.value.scrollTop = chatBox.value.scrollHeight;
            chatMessages.value.push({role:'ai',text:''});
            await streamChat(`${API}/api/news/${summaryModal.value.id}/chat`, msg, chatMessages, chatBox, chatLoading);
        };

        const sendRAGChat = async () => {
            if(!ragInput.value.trim()||ragLoading.value) return;
            const msg = ragInput.value.trim(); ragMessages.value.push({role:'user',text:msg}); ragInput.value = ''; ragLoading.value = true;
            await nextTick(); if(ragChatBox.value) ragChatBox.value.scrollTop = ragChatBox.value.scrollHeight;
            ragMessages.value.push({role:'ai',text:''});
            await streamChat(`${API}/api/chat`, msg, ragMessages, ragChatBox, ragLoading);
        };

        // 通用SSE流式聊天函数
        const streamChat = async (url, userMsg, messagesRef, boxRef, loadingRef) => {
            let aiText = '';
            const decoder = new TextDecoder();
            let buffer = '';
            try {
                const r = await fetch(url, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:userMsg})});
                if(!r.ok) { messagesRef.value[messagesRef.value.length-1].text = `请求失败 (${r.status})`; loadingRef.value = false; return; }
                const reader = r.body.getReader();
                while(true) {
                    const {done,value} = await reader.read(); if(done) break;
                    buffer += decoder.decode(value, {stream: true});
                    const lines = buffer.split('\n');
                    buffer = lines.pop();
                    for(const line of lines) {
                        if(line.startsWith('data: ')) {
                            const d = line.slice(6);
                            if(d === '[DONE]') continue;
                            try {
                                const j = JSON.parse(d);
                                if(j.text) { aiText += j.text; messagesRef.value[messagesRef.value.length-1].text = aiText; }
                            } catch(e) { console.warn('SSE parse error:', e, d); }
                        }
                    }
                    await nextTick(); if(boxRef.value) boxRef.value.scrollTop = boxRef.value.scrollHeight;
                }
                // 处理buffer残留数据
                if(buffer.trim()) {
                    for(const line of buffer.split('\n')) {
                        if(line.startsWith('data: ')) {
                            const d = line.slice(6);
                            if(d !== '[DONE]') { try { const j = JSON.parse(d); if(j.text) { aiText += j.text; messagesRef.value[messagesRef.value.length-1].text = aiText; } } catch(e) {} }
                        }
                    }
                }
            } catch(e) { messagesRef.value[messagesRef.value.length-1].text = '请求失败'; }
            loadingRef.value = false;
        };

        const batchSummary = async () => {
            if(batchLoading.value) return; batchLoading.value = true; batchProgress.value = '正在生成...'; showToast('开始批量生成AI总结...');
            let totalSuccess = 0;
            try {
                for(let round=0;round<5;round++) {
                    batchProgress.value = `第${round+1}轮...`;
                    const r = await fetch(`${API}/api/summary/batch`, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({limit:10})});
                    const data = await r.json(); totalSuccess += data.success||0;
                    if(data.processed===0) break;
                    showToast(`第${round+1}轮完成: ${data.success}条`); await loadNews();
                }
                showToast(`✅ 全部完成! 共生成${totalSuccess}条总结`);
            } catch(e) { showToast('批量总结失败','err'); }
            batchLoading.value = false; batchProgress.value = '';
        };

        const markRead = (n) => { if(!n.is_read) { fetch(`${API}/api/news/${n.id}/read`,{method:'POST'}); n.is_read=1; } };
        const openNews = (n) => { window.open(n.link,'_blank'); markRead(n); };
        const scrollToNews = (n) => {
            sortType.value = 'latest';
            filterSource.value = 'all';
            dateFilter.value = 'all';
            loadNews().then(() => {
                nextTick(() => {
                    const el = document.querySelector(`[data-news-id="${n.id}"]`);
                    if(el) {
                        el.scrollIntoView({behavior:'smooth', block:'center'});
                        el.classList.add('ring-2','ring-yellow-400/60');
                        setTimeout(() => el.classList.remove('ring-2','ring-yellow-400/60'), 3000);
                    } else {
                        window.open(n.link,'_blank');
                    }
                    markRead(n);
                });
            });
        };
        const manualRefresh = async () => { loading.value=true; await loadNews(); await loadStats(); showToast('已刷新'); };
        const triggerCollect = async () => {
            showToast('采集中...');
            try { const r=await(await fetch(`${API}/api/collect/trigger`,{method:'POST'})).json(); showToast(`新增${r.new_articles}条`); await loadNews(); await loadStats(); }
            catch(e) { showToast('失败','err'); }
        };
        const triggerScore = async () => {
            showToast('评分中...');
            try { const r=await(await fetch(`${API}/api/score/trigger`,{method:'POST'})).json(); showToast(`评分${r.scored}条`); await loadNews(); await loadStats(); }
            catch(e) { showToast('失败','err'); }
        };
        const addKeyword = () => { const kw=newKeyword.value.trim(); if(kw&&!blockedKeywords.value.includes(kw)){blockedKeywords.value.push(kw);newKeyword.value='';} };
        const loadConfig = async () => {
            try { const r=await(await fetch(`${API}/api/config/weights`)).json(); if(r&&Object.keys(r).length>0) weights.value=r; } catch(e) {}
            try {
                const r=await(await fetch(`${API}/api/config`)).json();
                if(r.blocked_keywords) blockedKeywords.value=JSON.parse(r.blocked_keywords);
                if(r.ai_model) aiModel.value=r.ai_model;
                if(r.refresh_interval) refreshInterval.value=parseInt(r.refresh_interval);
                if(r.collect_interval) collectInterval.value=parseInt(r.collect_interval);
                if(r.breaking_threshold) breakingThreshold.value=parseInt(r.breaking_threshold);
                if(r.breaking_types) breakingTypes.value=JSON.parse(r.breaking_types);
            } catch(e) {}
        };
        const saveSettings = async () => {
            try {
                await fetch(`${API}/api/config/weights`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(weights.value)});
                await fetch(`${API}/api/config`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
                    blocked_keywords:JSON.stringify(blockedKeywords.value),
                    ai_model:aiModel.value,
                    refresh_interval:String(refreshInterval.value),
                    collect_interval:String(collectInterval.value),
                    breaking_threshold:String(breakingThreshold.value),
                    breaking_types:JSON.stringify(breakingTypes.value)
                })});
                if(pollTimer) clearInterval(pollTimer);
                pollTimer = setInterval(() => loadNews(true), refreshInterval.value * 1000);
                if(collectTimer) clearInterval(collectTimer);
                collectTimer = setInterval(() => fetch(`${API}/api/collect/trigger`,{method:'POST'}), collectInterval.value * 1000);
                showSettings.value=false; showToast('已保存');
            } catch(e) { showToast('失败','err'); }
        };

        // 加载作者列表
        const loadAuthors = async (sourceType) => {
            try {
                const r = await fetch(`${API}/api/authors?source=${sourceType || 'all'}`);
                const data = await r.json();
                if(Array.isArray(data)) {
                    authorOptions.value = data;
                } else {
                    authorOptions.value = Object.values(data).flat();
                }
            } catch(e) { authorOptions.value = []; }
        };

        // 刷新特定人物的最新内容
        const refreshAuthor = async (author) => {
            showToast(`正在刷新 ${author}...`);
            try {
                const r = await fetch(`${API}/api/collect/trigger`, {method:'POST'});
                if(r.ok) {
                    setTimeout(() => { loadNews(true); showToast(`${author} 刷新完成`); }, 3000);
                }
            } catch(e) { showToast('刷新失败', 'err'); }
        };
        // 切换来源时重新加载作者列表并重置作者筛选
        const onSourceChange = (val) => {
            filterSource.value = val;
            filterAuthor.value = 'all';
            loadAuthors(val);
            loadNews();
        };

        // 弹窗打开时锁定页面滚动
        const isAnyModalOpen = computed(() => showSettings.value || summaryModal.value || showUpdatePanel.value || showRAGChat.value || showMarketBrief.value);
        watch(isAnyModalOpen, (v) => { document.body.style.overflow = v ? 'hidden' : ''; });

        // 鼠标跟随光晕
        const handleCardGlow = (e) => {
            const card = e.currentTarget;
            const rect = card.getBoundingClientRect();
            card.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`);
            card.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`);
        };
        const initCardGlow = () => {
            document.querySelectorAll('.news-card').forEach(card => {
                if (!card.querySelector('.card-glow')) {
                    const glow = document.createElement('div');
                    glow.className = 'card-glow';
                    card.appendChild(glow);
                }
                card.removeEventListener('mousemove', handleCardGlow);
                card.addEventListener('mousemove', handleCardGlow);
            });
        };

        // 评分环形SVG
        const getScoreRing = (score) => {
            const s = score || 0;
            const r = 16, c = 2 * Math.PI * r;
            const offset = c - (s / 100) * c;
            const color = s >= 90 ? '#ef4444' : s >= 80 ? '#f97316' : s >= 70 ? '#eab308' : s >= 50 ? '#22c55e' : s >= 30 ? '#3b82f6' : '#6b7280';
            return { r, c, offset, color };
        };

        onMounted(() => {
            loadTopNews(); loadNews(); loadStats(); loadConfig(); loadAuthors('all');
            pollTimer = setInterval(() => { loadNews(true); loadTopNews(); }, refreshInterval.value * 1000);
            // 点击外部关闭作者选择面板
            document.addEventListener('click', (e) => {
                if(showAuthorPicker.value && !e.target.closest('.relative')) {
                    showAuthorPicker.value = false;
                }
            });
            collectTimer = setInterval(() => fetch(`${API}/api/collect/trigger`,{method:'POST'}), collectInterval.value * 1000);
            // 初始化卡片光晕 + 每次加载后重新绑定
            nextTick(initCardGlow);
            watch(() => newsList.value.length, () => nextTick(initCardGlow));
            watch(() => topNews.value.length, () => nextTick(initCardGlow));
        });
        onUnmounted(() => { if(pollTimer) clearInterval(pollTimer); if(collectTimer) clearInterval(collectTimer); _timeouts.forEach(t => clearTimeout(t)); });

        return {
            newsList,topNews,topNewsIds,stats,sortType,filterSource,filterDirection,filterAuthor,dateFilter,searchText,loading,
            showSettings,settingsTab,weights,blockedKeywords,newKeyword,aiModel,toast,
            refreshInterval,collectInterval,showBreakingBanner,breakingThreshold,breakingTypes,showNewNotif,
            breakingNews,updateToast,showUpdatePanel,updateList,
            summaryModal,summaryFocus,chatMessages,chatInput,chatLoading,chatBox,
            showRAGChat,ragMessages,ragInput,ragLoading,ragChatBox,
            batchLoading,batchProgress,
            analysisTab,analysisData,analysisLoading,showMarketBrief,marketBriefText,marketBriefLoading,
            sourceOptions,dateOptions,directionOptions,focusOptions,breakingTypeOptions,
            authorOptions,showAuthorPicker,authorListRef,groupedAuthors,authorLetters,scrollToLetter,
            filteredNews,getScoreLevel,getScoreColor,getScoreRing,truncate,
            getSourceTagClass,timeAgo,formatPubTime,formatLocalTime,formatSummary,
            openSummary,regenerateSummary,loadAnalysis,openMarketBrief,toggleBookmark,sendChat,sendRAGChat,batchSummary,markRead,openNews,scrollToNews,
            loadNews,doSearch,manualRefresh,triggerCollect,triggerScore,onSourceChange,refreshAuthor,
            addKeyword,saveSettings,showToast
        };
    }
}).mount('#app');
