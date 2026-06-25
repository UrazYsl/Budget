const API = '/api'

function app() {
    return {
        page: 'dashboard',
        theme: 'dark',
        sidebarOpen: false,

        // shared
        accounts: [],
        categories: [],

        // accounts view
        accountForm: { show: false, editing: null, name: '' },

        // categories view
        categoryForm: { show: false, editing: null, name: '' },

        // transactions view
        transactions: [],
        txFilters: {
            account_id: '', category_id: '', type: '',
            start_date: '', end_date: '',
            min_amount: '', max_amount: '',
            limit: 50, offset: 0,
        },
        txForm: {
            show: false, editing: null,
            date: '', amount: '', type: 'expense',
            account_id: '', category_id: '', receiptFile: null,
        },

        // budgets
        budgets: [],
        budgetForm: { show: false, budget_id: null, category_id: null, category_name: '', amount: '' },

        // recurring view
        recurringList: [],
        recurringForm: {
            show: false, editing: null,
            amount: '', type: 'expense', recurring_interval: 'monthly',
            next_run_date: '', account_id: '', category_id: '',
        },

        // dashboard
        dash: {
            year: new Date().getFullYear(),
            month: new Date().getMonth() + 1,
            summary: null,
            prevSummary: null,
            balances: [],
            catTotals: [],
            upcoming: [],
        },

        // settings
        timezone: '',
        allTimezones: [],
        tzSearch: '',
        tzPicked: '',
        tzSaveStatus: '',

        // clock
        nowStr: '',
        clockInterval: null,

        // ── theme ──

        toggleTheme() {
            this.theme = this.theme === 'dark' ? 'light' : 'dark'
            localStorage.setItem('theme', this.theme)
            document.documentElement.setAttribute('data-theme', this.theme)
        },

        // ── init ──

        async init() {
            this.theme = document.documentElement.getAttribute('data-theme') || 'dark'
            this.allTimezones = Intl.supportedValuesOf('timeZone')
            await Promise.all([this.loadAccounts(), this.loadCategories(), this.loadBudgets(), this.loadSettings()])

            const saved = localStorage.getItem('txFilters')
            if (saved) {
                const parsed = JSON.parse(saved)
                this.txFilters = { ...this.txFilters, ...parsed, offset: 0 }
            }

            history.replaceState({ page: this.page }, '')
            this._lastPushed = this.page

            window.addEventListener('popstate', e => {
                if (e.state?.page) {
                    this._lastPushed = e.state.page
                    this.page = e.state.page
                }
            })

            this.$watch('page', val => {
                if (val !== this._lastPushed) {
                    this._lastPushed = val
                    history.pushState({ page: val }, '')
                }
                if (val !== 'dashboard') this.stopClock()
                if (val === 'transactions') this.loadTransactions()
                if (val === 'accounts')     this.loadAccounts()
                if (val === 'categories')   this.loadCategories()
                if (val === 'recurring')    this.loadRecurring()
                if (val === 'dashboard')    this.loadDashboard()
                if (val === 'settings')     this.loadSettings()
            })

            this.loadDashboard()
        },

        // ── shared ──

        async loadAccounts() {
            const res = await fetch(`${API}/accounts`)
            this.accounts = await res.json()
        },

        async loadCategories() {
            const res = await fetch(`${API}/categories`)
            this.categories = await res.json()
        },

        accountName(id) { return this.accounts.find(a => a.id === id)?.name ?? '—' },
        categoryName(id) { return this.categories.find(c => c.id === id)?.name ?? '—' },

        // ── accounts ──

        openAccountForm() {
            this.accountForm = { show: true, editing: null, name: '' }
        },

        editAccount(a) {
            this.accountForm = { show: true, editing: a.id, name: a.name }
        },

        async saveAccount() {
            if (this.accountForm.editing) {
                await fetch(`${API}/accounts/${this.accountForm.editing}?new_name=${encodeURIComponent(this.accountForm.name)}`, { method: 'PUT' })
            } else {
                await fetch(`${API}/accounts`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: this.accountForm.name }),
                })
            }
            this.accountForm.show = false
            await this.loadAccounts()
        },

        async deleteAccount(id) {
            if (!confirm('Delete this account? All associated transactions will also be deleted.')) return
            await fetch(`${API}/accounts/${id}`, { method: 'DELETE' })
            await this.loadAccounts()
        },

        // ── categories ──

        openCategoryForm() {
            this.categoryForm = { show: true, editing: null, name: '' }
        },

        editCategory(c) {
            this.categoryForm = { show: true, editing: c.id, name: c.name }
        },

        async saveCategory() {
            if (this.categoryForm.editing) {
                await fetch(`${API}/categories/${this.categoryForm.editing}?new_name=${encodeURIComponent(this.categoryForm.name)}`, { method: 'PUT' })
            } else {
                await fetch(`${API}/categories`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: this.categoryForm.name }),
                })
            }
            this.categoryForm.show = false
            await this.loadCategories()
        },

        async deleteCategory(id) {
            if (!confirm('Delete this category? Transactions will be reassigned to Misc.')) return
            await fetch(`${API}/categories/${id}`, { method: 'DELETE' })
            await this.loadCategories()
        },

        // ── budgets ──

        async loadBudgets() {
            const res = await fetch(`${API}/budgets`)
            this.budgets = await res.json()
        },

        budgetFor(category_id) {
            return this.budgets.find(b => b.category_id === category_id) ?? null
        },

        openBudgetForm(cat) {
            const existing = this.budgetFor(cat.id)
            this.budgetForm = {
                show: true,
                budget_id: existing?.id ?? null,
                category_id: cat.id,
                category_name: cat.name,
                amount: existing ? existing.amount : '',
            }
        },

        async saveBudget() {
            await fetch(`${API}/budgets`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ category_id: this.budgetForm.category_id, amount: parseFloat(this.budgetForm.amount) }),
            })
            this.budgetForm.show = false
            await this.loadBudgets()
        },

        async deleteBudget() {
            if (!this.budgetForm.budget_id) return
            await fetch(`${API}/budgets/${this.budgetForm.budget_id}`, { method: 'DELETE' })
            this.budgetForm.show = false
            await this.loadBudgets()
        },

        // ── transactions ──

        async loadTransactions() {
            const p = new URLSearchParams()
            if (this.txFilters.account_id)  p.set('account_id',  this.txFilters.account_id)
            if (this.txFilters.category_id) p.set('category_id', this.txFilters.category_id)
            if (this.txFilters.type)        p.set('type',        this.txFilters.type)
            if (this.txFilters.start_date)  p.set('start_date',  this.txFilters.start_date)
            if (this.txFilters.end_date)    p.set('end_date',    this.txFilters.end_date)
            if (this.txFilters.min_amount)  p.set('min_amount',  this.txFilters.min_amount)
            if (this.txFilters.max_amount)  p.set('max_amount',  this.txFilters.max_amount)
            p.set('limit',  this.txFilters.limit)
            p.set('offset', this.txFilters.offset)
            const res = await fetch(`${API}/transactions?${p}`)
            this.transactions = await res.json()
            localStorage.setItem('txFilters', JSON.stringify(this.txFilters))
        },

        applyTxFilters() { this.txFilters.offset = 0; this.loadTransactions() },

        resetTxFilters() {
            this.txFilters = { account_id: '', category_id: '', type: '', start_date: '', end_date: '', min_amount: '', max_amount: '', limit: 50, offset: 0 }
            localStorage.removeItem('txFilters')
            this.loadTransactions()
        },

        async exportCsv() {
            const p = new URLSearchParams()
            if (this.txFilters.account_id)  p.set('account_id',  this.txFilters.account_id)
            if (this.txFilters.category_id) p.set('category_id', this.txFilters.category_id)
            if (this.txFilters.type)        p.set('type',        this.txFilters.type)
            if (this.txFilters.start_date)  p.set('start_date',  this.txFilters.start_date)
            if (this.txFilters.end_date)    p.set('end_date',    this.txFilters.end_date)
            if (this.txFilters.min_amount)  p.set('min_amount',  this.txFilters.min_amount)
            if (this.txFilters.max_amount)  p.set('max_amount',  this.txFilters.max_amount)
            const res = await fetch(`${API}/transactions?${p}`)
            const all = await res.json()
            const rows = [['Date', 'Amount', 'Type', 'Account', 'Category']]
            for (const tx of all) {
                rows.push([tx.date, tx.amount.toFixed(2), tx.type, this.accountName(tx.account_id), this.categoryName(tx.category_id)])
            }
            const csv = rows.map(r => r.map(v => `"${v}"`).join(',')).join('\n')
            const a = Object.assign(document.createElement('a'), {
                href: URL.createObjectURL(new Blob([csv], { type: 'text/csv' })),
                download: `transactions${this.txFilters.start_date ? '_' + this.txFilters.start_date : ''}.csv`,
            })
            a.click()
            URL.revokeObjectURL(a.href)
        },

        txPrevPage() {
            this.txFilters.offset = Math.max(0, this.txFilters.offset - this.txFilters.limit)
            this.loadTransactions()
        },

        txNextPage() {
            this.txFilters.offset += this.txFilters.limit
            this.loadTransactions()
        },

        openTxForm() {
            this.txForm = {
                show: true, editing: null,
                date: new Date().toISOString().split('T')[0],
                amount: '', type: 'expense',
                account_id: this.accounts[0]?.id ?? '',
                category_id: this.categories[0]?.id ?? '',
                receiptFile: null,
            }
        },

        editTx(tx) {
            this.txForm = {
                show: true, editing: tx.id,
                date: tx.date, amount: tx.amount, type: tx.type,
                account_id: tx.account_id, category_id: tx.category_id,
                receiptFile: null,
            }
        },

        async saveTx() {
            const body = {
                date: this.txForm.date,
                amount: parseFloat(this.txForm.amount),
                type: this.txForm.type,
                account_id: parseInt(this.txForm.account_id),
                category_id: parseInt(this.txForm.category_id),
            }
            if (this.txForm.editing) {
                await fetch(`${API}/transactions/${this.txForm.editing}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body),
                })
            } else {
                const res = await fetch(`${API}/transactions`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body),
                })
                const created = await res.json()
                if (this.txForm.receiptFile) {
                    const fd = new FormData()
                    fd.append('file', this.txForm.receiptFile)
                    await fetch(`${API}/transactions/${created.id}/receipt`, { method: 'POST', body: fd })
                }
            }
            this.txForm.show = false
            await this.loadTransactions()
        },

        async deleteTx(id) {
            if (!confirm('Delete this transaction?')) return
            await fetch(`${API}/transactions/${id}`, { method: 'DELETE' })
            await this.loadTransactions()
        },

        // ── recurring ──

        async loadRecurring() {
            const res = await fetch(`${API}/recurring_transactions`)
            this.recurringList = await res.json()
        },

        openRecurringForm() {
            this.recurringForm = {
                show: true, editing: null,
                amount: '', type: 'expense', recurring_interval: 'monthly',
                next_run_date: new Date().toISOString().split('T')[0],
                account_id: this.accounts[0]?.id ?? '',
                category_id: this.categories[0]?.id ?? '',
            }
        },

        editRecurring(r) {
            this.recurringForm = {
                show: true, editing: r.id,
                amount: r.amount, type: r.type,
                recurring_interval: r.recurring_interval,
                next_run_date: r.next_run_date,
                account_id: r.account_id, category_id: r.category_id,
            }
        },

        async saveRecurring() {
            const body = {
                amount: parseFloat(this.recurringForm.amount),
                type: this.recurringForm.type,
                recurring_interval: this.recurringForm.recurring_interval,
                next_run_date: this.recurringForm.next_run_date,
                account_id: parseInt(this.recurringForm.account_id),
                category_id: parseInt(this.recurringForm.category_id),
            }
            if (this.recurringForm.editing) {
                await fetch(`${API}/recurring_transactions/${this.recurringForm.editing}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body),
                })
            } else {
                await fetch(`${API}/recurring_transactions`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(body),
                })
            }
            this.recurringForm.show = false
            await this.loadRecurring()
        },

        async deleteRecurring(id) {
            if (!confirm('Delete this recurring transaction?')) return
            await fetch(`${API}/recurring_transactions/${id}`, { method: 'DELETE' })
            await this.loadRecurring()
        },

        async runRecurringNow() {
            const res = await fetch(`${API}/recurring_transactions/run`, { method: 'POST' })
            const data = await res.json()
            alert(`Created ${data.created} transaction(s).`)
            await this.loadRecurring()
        },

        // ── dashboard ──

        netRingStyle() {
            const s = this.dash.summary
            if (!s || (s.total_income === 0 && s.total_expenses === 0)) {
                return 'background: conic-gradient(var(--income) 0% 100%)'
            }
            const total = s.total_income + s.total_expenses
            const pct = (s.total_income / total * 100).toFixed(2)
            return `background: conic-gradient(var(--income) 0% ${pct}%, var(--expense) ${pct}% 100%)`
        },

        goToAccount(account_id) {
            const y = this.dash.year
            const m = this.dash.month
            const pad = n => String(n).padStart(2, '0')
            const firstDay = `${y}-${pad(m)}-01`
            const lastDay = `${y}-${pad(m)}-${pad(new Date(y, m, 0).getDate())}`
            this.txFilters = { ...this.txFilters, account_id, type: '', category_id: '', start_date: firstDay, end_date: lastDay, offset: 0 }
            this.page = 'transactions'
            this.loadTransactions()
        },

        goToCategory(category_id) {
            const y = this.dash.year
            const m = this.dash.month
            const pad = n => String(n).padStart(2, '0')
            const firstDay = `${y}-${pad(m)}-01`
            const lastDay = `${y}-${pad(m)}-${pad(new Date(y, m, 0).getDate())}`
            this.txFilters = { ...this.txFilters, category_id, type: '', account_id: '', start_date: firstDay, end_date: lastDay, offset: 0 }
            this.page = 'transactions'
            this.loadTransactions()
        },

        goToFiltered(type) {
            const y = this.dash.year
            const m = this.dash.month
            const pad = n => String(n).padStart(2, '0')
            const firstDay = `${y}-${pad(m)}-01`
            const lastDayNum = new Date(y, m, 0).getDate()
            const lastDay = `${y}-${pad(m)}-${pad(lastDayNum)}`
            this.txFilters = { ...this.txFilters, type, start_date: firstDay, end_date: lastDay, account_id: '', category_id: '', offset: 0 }
            this.page = 'transactions'
            this.loadTransactions()
        },

        prevMonth() {
            const m = this.dash.month === 1 ? 12 : this.dash.month - 1
            const y = this.dash.month === 1 ? this.dash.year - 1 : this.dash.year
            return { year: y, month: m }
        },

        momLabel(current, prev) {
            if (prev == null || prev === 0) return null
            const pct = (current - prev) / prev * 100
            return (pct >= 0 ? '+' : '') + pct.toFixed(0) + '% vs last month'
        },

        momColor(current, prev, higherIsBad = false) {
            if (prev == null || prev === 0) return 'var(--text-muted)'
            const isHigher = current > prev
            const isGood = higherIsBad ? !isHigher : isHigher
            return isGood ? 'var(--income)' : 'var(--expense)'
        },

        async loadUpcoming() {
            const res = await fetch(`${API}/summary/upcoming`)
            this.dash.upcoming = await res.json()
        },

        async loadDashboard() {
            const prev = this.prevMonth()
            const [summRes, prevSummRes, balRes, catRes] = await Promise.all([
                fetch(`${API}/summary/monthly?year=${this.dash.year}&month=${this.dash.month}`),
                fetch(`${API}/summary/monthly?year=${prev.year}&month=${prev.month}`),
                fetch(`${API}/summary/accounts`),
                fetch(`${API}/summary/categories?year=${this.dash.year}&month=${this.dash.month}`),
                this.loadBudgets(),
                this.loadUpcoming(),
            ])
            this.dash.summary = await summRes.json()
            this.dash.prevSummary = await prevSummRes.json()
            this.dash.balances = await balRes.json()
            this.dash.catTotals = await catRes.json()
            this.startClock()
        },

        downloadBackup() {
            window.location.href = `${API}/backup/db`
        },

        startClock() {
            this.stopClock()
            const tick = () => {
                const tz = this.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone
                this.nowStr = new Intl.DateTimeFormat('en-GB', {
                    timeZone: tz,
                    weekday: 'long',
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false,
                }).format(new Date())
            }
            tick()
            this.clockInterval = setInterval(tick, 1000)
        },

        stopClock() {
            if (this.clockInterval) {
                clearInterval(this.clockInterval)
                this.clockInterval = null
            }
        },

        // ── settings ──

        async loadSettings() {
            const res = await fetch(`${API}/settings`)
            const data = await res.json()
            this.timezone = data.timezone
            this.tzSearch = ''
            this.tzPicked = ''
            this.tzSaveStatus = ''
        },

        filteredTimezones() {
            if (!this.tzSearch || this.tzSearch === this.tzPicked) return []
            const q = this.tzSearch.toLowerCase()
            return this.allTimezones.filter(tz => tz.toLowerCase().includes(q)).slice(0, 8)
        },

        async pickTimezone(tz) {
            this.tzPicked = tz
            this.tzSearch = tz
            this.tzSaveStatus = 'saving'
            const res = await fetch(`${API}/settings`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ timezone: tz }),
            })
            if (res.ok) {
                this.timezone = tz
                this.tzSaveStatus = 'saved'
                this.startClock()
            } else {
                this.tzSaveStatus = 'error'
            }
        },
    }
}
