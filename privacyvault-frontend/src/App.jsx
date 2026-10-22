import RealHEDemo from "./RealHEDemo";
import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import api from "./api";
import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Calculator,
  CheckCircle2,
  Database,
  KeyRound,
  Lock,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
  Unlock,
  Users,
  XCircle,
} from "lucide-react";

const BACKEND_URL = (
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
).replace(/\/+$/, "");

const API_BASE = `${BACKEND_URL}/api/v1`;


const glassCard =
  "rounded-2xl border border-white/10 bg-slate-950/50 p-5 shadow-2xl shadow-black/20 backdrop-blur-xl";

function MetricCard({ icon: Icon, iconClass, label, value, subtitle }) {
  return (
    <motion.div
      whileHover={{ y: -4 }}
      className={`${glassCard} transition-colors hover:border-emerald-400/30`}
    >
      <div className="flex items-center gap-4">
        <div className={`rounded-xl p-3 ${iconClass}`}>
          <Icon className="h-7 w-7" />
        </div>
        <div>
          <p className="text-xs uppercase tracking-wider text-slate-400">{label}</p>
          <p className="mt-1 text-2xl font-bold text-white">{value}</p>
          {subtitle && <p className="mt-1 text-xs text-slate-500">{subtitle}</p>}
        </div>
      </div>
    </motion.div>
  );
}

function JourneyStep({ number, icon: Icon, title, description, content, active }) {
  return (
    <div className="relative flex flex-1 flex-col items-center text-center">
      <div
        className={`flex h-14 w-14 items-center justify-center rounded-full border transition-all ${
          active
            ? "border-emerald-300 bg-emerald-500 text-slate-950 shadow-lg shadow-emerald-500/30"
            : "border-slate-700 bg-slate-900 text-slate-400"
        }`}
      >
        <Icon className="h-6 w-6" />
      </div>
      <p className="mt-3 text-xs font-semibold text-emerald-300">STEP {number}</p>
      <h3 className="mt-1 font-semibold text-white">{title}</h3>
      <p className="mt-1 max-w-[170px] text-xs leading-5 text-slate-400">{description}</p>
      <div className="mt-3 min-h-12 w-full rounded-lg border border-white/5 bg-black/30 p-2 font-mono text-[10px] leading-4 text-emerald-300">
        {content}
      </div>
    </div>
  );
}

function App() {
  const [stats, setStats] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [backendStatus, setBackendStatus] = useState("Checking backend...");
  const [form, setForm] = useState({
    employee_id: "",
    name: "",
    department: "Engineering",
    position: "",
    salary: "",
  });
  const [formMessage, setFormMessage] = useState("");
  const [operation, setOperation] = useState("average");
  const [department, setDepartment] = useState("");
  const [result, setResult] = useState(null);
  const [computeLoading, setComputeLoading] = useState(false);
  const [breachMode, setBreachMode] = useState(false);
  const [journeyStarted, setJourneyStarted] = useState(false);

  const departments = useMemo(() => {
    const fromStats = stats?.departments ?? [];
    const fromEmployees = employees.map((employee) => employee.department);
    return [...new Set([...fromStats, ...fromEmployees])].filter(Boolean);
  }, [stats, employees]);

  async function loadData() {
    setLoading(true);

    try {
      const [healthResponse, statsResponse, employeesResponse] = await Promise.all([
        api.get(`${BACKEND_URL}/health`),
        api.get(`${API_BASE}/analytics/dashboard`),
        api.get(`${API_BASE}/employees/`),
      ]);

      setBackendStatus(
        healthResponse.data.status === "healthy"
          ? "Backend connected • encrypted analytics ready"
          : "Backend reachable"
      );
      setStats(statsResponse.data);
      setEmployees(employeesResponse.data.employees ?? []);
    } catch (error) {
      console.error(error);
      setBackendStatus(
        "Backend unavailable. Check the configured API address and service status."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function addEmployee(event) {
    event.preventDefault();
    setFormMessage("");

    try {
      await api.post(`${API_BASE}/employees/`, {
        ...form,
        salary: Number(form.salary),
      });

      setFormMessage("Employee saved. The salary is stored as encrypted ciphertext.");
      setForm({
        employee_id: "",
        name: "",
        department: "Engineering",
        position: "",
        salary: "",
      });
      await loadData();
    } catch (error) {
      const message =
        error.response?.data?.detail ||
        "Could not save employee. Check the backend terminal.";
      setFormMessage(message);
    }
  }

  async function compute() {
    setComputeLoading(true);
    setResult(null);

    try {
      const response = await api.post(`${API_BASE}/computations/compute`, {
        operation,
        department: department || null,
      });
      setResult(response.data);
      await loadData();
    } catch (error) {
      setResult({
        error:
          error.response?.data?.detail ||
          "Computation failed. Add at least one employee first.",
      });
    } finally {
      setComputeLoading(false);
    }
  }

  const traditionalRecords = [
    ["Employee A", "₹75,000"],
    ["Employee B", "₹52,000"],
    ["Employee C", "₹90,000"],
  ];

  const protectedRecords = [
    ["Employee A", "9A7F34C8D91E..."],
    ["Employee B", "B42E19F73AC2..."],
    ["Employee C", "72D8AF91E452..."],
  ];

  return (
    <main className="min-h-screen text-slate-100">
      <header className="sticky top-0 z-20 border-b border-white/10 bg-slate-950/75 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-5 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="rounded-xl border border-emerald-300/30 bg-emerald-400/10 p-2.5">
              <ShieldCheck className="h-7 w-7 text-emerald-300" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white">
                Privacy<span className="text-emerald-300">Vault</span>
              </h1>
              <p className="text-xs text-slate-400">
                Privacy-Preserving Computation Playground
              </p>
            </div>
          </div>

          <div className="hidden rounded-full border border-emerald-400/20 bg-emerald-500/10 px-4 py-2 text-xs text-emerald-200 sm:block">
            <span className="mr-2 inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
            {backendStatus}
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-5 py-10">
      <RealHEDemo />
        <div className="mb-10 grid gap-8 lg:grid-cols-[1.3fr_0.7fr] lg:items-center">
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-500/10 px-4 py-2 text-sm text-emerald-200">
              <Lock className="h-4 w-4" />
              Privacy-first salary analytics
            </div>

            <h2 className="max-w-3xl text-4xl font-black leading-tight tracking-tight text-white sm:text-5xl">
              Compute useful salary insights without exposing individual salaries.
            </h2>

            <p className="mt-5 max-w-2xl text-base leading-7 text-slate-300">
              PrivacyVault demonstrates how encrypted salary records can be stored,
              aggregated, and converted into authorized final results while showing
              only ciphertext to untrusted viewers.
            </p>

            <div className="mt-6 flex flex-wrap gap-3">
              <button
                onClick={() => setJourneyStarted(true)}
                className="rounded-xl bg-emerald-400 px-5 py-3 font-semibold text-slate-950 transition hover:bg-emerald-300"
              >
                Start encryption journey
              </button>
              <button
                onClick={loadData}
                className="inline-flex items-center gap-2 rounded-xl border border-white/15 px-5 py-3 font-semibold text-white transition hover:bg-white/10"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                Refresh dashboard
              </button>
            </div>
          </div>

          <div className={`${glassCard} overflow-hidden`}>
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Privacy protection score</p>
                <p className="mt-1 text-4xl font-black text-emerald-300">
                  {stats?.privacy_score ?? 100}
                  <span className="text-xl text-slate-500">/100</span>
                </p>
              </div>
              <KeyRound className="h-14 w-14 text-emerald-300/80" />
            </div>

            <div className="h-3 overflow-hidden rounded-full bg-slate-800">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${stats?.privacy_score ?? 100}%` }}
                className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-cyan-300"
              />
            </div>

            <div className="mt-5 space-y-2 text-sm">
              <p className="flex items-center gap-2 text-emerald-100">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                Data encrypted before protected storage
              </p>
              <p className="flex items-center gap-2 text-emerald-100">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                Individual salaries hidden from the dashboard
              </p>
              <p className="flex items-center gap-2 text-emerald-100">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                Only an aggregate result is revealed
              </p>
            </div>
          </div>
        </div>

        <section className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            icon={Users}
            iconClass="bg-emerald-400/10 text-emerald-300"
            label="Employees"
            value={stats?.total_employees ?? 0}
            subtitle="Contributing encrypted records"
          />
          <MetricCard
            icon={Database}
            iconClass="bg-cyan-400/10 text-cyan-300"
            label="Ciphertext records"
            value={stats?.total_encrypted_records ?? 0}
            subtitle="No plaintext salary column"
          />
          <MetricCard
            icon={Calculator}
            iconClass="bg-violet-400/10 text-violet-300"
            label="Computations"
            value={stats?.total_computations ?? 0}
            subtitle="Encrypted aggregation requests"
          />
          <MetricCard
            icon={Activity}
            iconClass="bg-amber-400/10 text-amber-300"
            label="Scheme"
            value={stats?.encryption_scheme ?? "CKKS"}
            subtitle="Simulation mode for this Mac demo"
          />
        </section>

        <section className={`${glassCard} mb-8`}>
          <div className="mb-7 flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-emerald-300">INTERACTIVE VISUALIZATION</p>
              <h2 className="mt-1 text-2xl font-bold text-white">Encryption journey</h2>
              <p className="mt-1 text-sm text-slate-400">
                Follow one salary through the privacy-preserving workflow.
              </p>
            </div>
            <button
              onClick={() => setJourneyStarted((current) => !current)}
              className="rounded-lg border border-emerald-400/25 bg-emerald-500/10 px-4 py-2 text-sm font-semibold text-emerald-200 hover:bg-emerald-500/20"
            >
              {journeyStarted ? "Reset journey" : "Run journey"}
            </button>
          </div>

          <div className="grid gap-6 md:grid-cols-5">
            <JourneyStep
              number="01"
              icon={Unlock}
              title="Plaintext input"
              description="The employee enters a confidential salary."
              content={journeyStarted ? "₹75,000" : "Waiting for input"}
              active={journeyStarted}
            />
            <JourneyStep
              number="02"
              icon={Lock}
              title="Encrypt"
              description="The sensitive value becomes protected ciphertext."
              content={journeyStarted ? "ENC: 9A7F34C8D91E..." : "Locked"}
              active={journeyStarted}
            />
            <JourneyStep
              number="03"
              icon={Database}
              title="Store"
              description="The server database receives ciphertext only."
              content={journeyStarted ? "SQLite → encrypted_salary" : "No record"}
              active={journeyStarted}
            />
            <JourneyStep
              number="04"
              icon={Calculator}
              title="Aggregate"
              description="The system performs supported aggregate operations."
              content={journeyStarted ? "Enc(A) + Enc(B) + Enc(C)" : "No computation"}
              active={journeyStarted}
            />
            <JourneyStep
              number="05"
              icon={TrendingUp}
              title="Reveal result"
              description="Only an authorized aggregate outcome is shown."
              content={journeyStarted ? "Average: ₹72,333" : "Aggregate only"}
              active={journeyStarted}
            />
          </div>
        </section>

        <section className="mb-8 grid gap-8 xl:grid-cols-2">
          <div className={glassCard}>
            <div className="mb-6 flex items-center gap-3">
              <Users className="h-6 w-6 text-emerald-300" />
              <div>
                <h2 className="text-xl font-bold text-white">Add protected employee data</h2>
                <p className="text-sm text-slate-400">
                  The API stores the salary in the encrypted salary field.
                </p>
              </div>
            </div>

            <form onSubmit={addEmployee} className="grid gap-4 sm:grid-cols-2">
              <input
                required
                value={form.employee_id}
                onChange={(event) => setForm({ ...form, employee_id: event.target.value })}
                placeholder="Employee ID (e.g. EMP001)"
                className="rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none placeholder:text-slate-500 focus:border-emerald-400"
              />
              <input
                required
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                placeholder="Employee name"
                className="rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none placeholder:text-slate-500 focus:border-emerald-400"
              />
              <select
                value={form.department}
                onChange={(event) => setForm({ ...form, department: event.target.value })}
                className="rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none focus:border-emerald-400"
              >
                <option>Engineering</option>
                <option>Sales</option>
                <option>Marketing</option>
                <option>Finance</option>
                <option>Human Resources</option>
              </select>
              <input
                required
                value={form.position}
                onChange={(event) => setForm({ ...form, position: event.target.value })}
                placeholder="Position"
                className="rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none placeholder:text-slate-500 focus:border-emerald-400"
              />
              <input
                required
                min="1"
                type="number"
                value={form.salary}
                onChange={(event) => setForm({ ...form, salary: event.target.value })}
                placeholder="Salary in ₹"
                className="rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none placeholder:text-slate-500 focus:border-emerald-400 sm:col-span-2"
              />
              <button
                type="submit"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-400 px-5 py-3 font-bold text-slate-950 transition hover:bg-emerald-300 sm:col-span-2"
              >
                <Lock className="h-4 w-4" />
                Encrypt and save employee salary
              </button>
            </form>

            {formMessage && (
              <p className="mt-4 rounded-xl border border-emerald-400/20 bg-emerald-500/10 p-3 text-sm text-emerald-100">
                {formMessage}
              </p>
            )}
          </div>

          <div className={glassCard}>
            <div className="mb-6 flex items-center gap-3">
              <Calculator className="h-6 w-6 text-cyan-300" />
              <div>
                <h2 className="text-xl font-bold text-white">Computation playground</h2>
                <p className="text-sm text-slate-400">
                  Request an authorized aggregate without showing each salary.
                </p>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <select
                value={operation}
                onChange={(event) => setOperation(event.target.value)}
                className="rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none focus:border-cyan-300"
              >
                <option value="average">Average salary</option>
                <option value="sum">Total salary expenditure</option>
                <option value="count">Employee count</option>
              </select>

              <select
                value={department}
                onChange={(event) => setDepartment(event.target.value)}
                className="rounded-xl border border-white/10 bg-slate-900 px-4 py-3 text-white outline-none focus:border-cyan-300"
              >
                <option value="">All departments</option>
                {departments.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>

              <button
                onClick={compute}
                disabled={computeLoading}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-cyan-300 px-5 py-3 font-bold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-50 sm:col-span-2"
              >
                {computeLoading ? (
                  <RefreshCw className="h-4 w-4 animate-spin" />
                ) : (
                  <Calculator className="h-4 w-4" />
                )}
                {computeLoading ? "Computing..." : "Compute protected result"}
              </button>
            </div>

            {result && (
              <div className="mt-5 rounded-xl border border-cyan-300/20 bg-cyan-400/5 p-4">
                {result.error ? (
                  <p className="text-sm text-red-300">{result.error}</p>
                ) : (
                  <>
                    <p className="text-xs font-semibold tracking-wider text-cyan-200">
                      AUTHORIZED AGGREGATE RESULT
                    </p>
                    <p className="mt-2 text-3xl font-black text-white">
                      {result.computation_type === "count"
                        ? result.decrypted_result
                        : `₹${Number(result.decrypted_result).toLocaleString("en-IN", {
                            maximumFractionDigits: 2,
                          })}`}
                    </p>
                    <div className="mt-4 grid grid-cols-3 gap-3 text-center text-xs">
                      <div className="rounded-lg bg-black/20 p-2">
                        <p className="text-slate-500">Records</p>
                        <p className="mt-1 font-bold text-white">{result.employee_count}</p>
                      </div>
                      <div className="rounded-lg bg-black/20 p-2">
                        <p className="text-slate-500">Privacy</p>
                        <p className="mt-1 font-bold text-emerald-300">{result.privacy_score}/100</p>
                      </div>
                      <div className="rounded-lg bg-black/20 p-2">
                        <p className="text-slate-500">Time</p>
                        <p className="mt-1 font-bold text-white">
                          {Number(result.computation_time_ms).toFixed(1)} ms
                        </p>
                      </div>
                    </div>
                    <p className="mt-4 break-all rounded-lg bg-black/30 p-3 font-mono text-[10px] text-cyan-200">
                      Encrypted result preview: {result.encrypted_result_preview}
                    </p>
                  </>
                )}
              </div>
            )}
          </div>
        </section>

        <section className={`${glassCard} mb-8`}>
          <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-amber-300">PRIVACY ATTACK SIMULATOR</p>
              <h2 className="mt-1 text-2xl font-bold text-white">
                What if the database is breached?
              </h2>
              <p className="mt-1 text-sm text-slate-400">
                Compare the information an attacker sees in a traditional versus protected system.
              </p>
            </div>
            <button
              onClick={() => setBreachMode((current) => !current)}
              className={`inline-flex items-center gap-2 rounded-xl px-4 py-3 font-bold transition ${
                breachMode
                  ? "bg-red-500 text-white hover:bg-red-400"
                  : "bg-amber-300 text-slate-950 hover:bg-amber-200"
              }`}
            >
              <AlertTriangle className="h-4 w-4" />
              {breachMode ? "Hide breach simulation" : "Simulate data breach"}
            </button>
          </div>

          <div className="grid gap-5 lg:grid-cols-2">
            <div className="rounded-xl border border-red-400/20 bg-red-500/5 p-5">
              <div className="mb-4 flex items-center gap-2 text-red-300">
                <XCircle className="h-5 w-5" />
                <h3 className="font-bold">Traditional system</h3>
              </div>
              <p className="mb-4 text-sm text-slate-400">
                Salaries stored as readable plaintext.
              </p>
              <div className="space-y-2">
                {traditionalRecords.map(([employee, value]) => (
                  <div
                    key={employee}
                    className="flex items-center justify-between rounded-lg border border-red-400/10 bg-black/20 px-4 py-3"
                  >
                    <span className="text-sm text-slate-200">{employee}</span>
                    <span className={`font-mono text-sm ${breachMode ? "text-red-300" : "text-slate-600"}`}>
                      {breachMode ? value : "••••••••"}
                    </span>
                  </div>
                ))}
              </div>
              {breachMode && (
                <p className="mt-4 text-sm text-red-200">
                  Exposed: an attacker can read every employee’s salary.
                </p>
              )}
            </div>

            <div className="rounded-xl border border-emerald-400/20 bg-emerald-500/5 p-5">
              <div className="mb-4 flex items-center gap-2 text-emerald-300">
                <CheckCircle2 className="h-5 w-5" />
                <h3 className="font-bold">PrivacyVault system</h3>
              </div>
              <p className="mb-4 text-sm text-slate-400">
                Salary storage shows ciphertext, not readable values.
              </p>
              <div className="space-y-2">
                {protectedRecords.map(([employee, value]) => (
                  <div
                    key={employee}
                    className="flex items-center justify-between rounded-lg border border-emerald-400/10 bg-black/20 px-4 py-3"
                  >
                    <span className="text-sm text-slate-200">{employee}</span>
                    <span className="font-mono text-sm text-emerald-300">
                      {breachMode ? value : "••••••••"}
                    </span>
                  </div>
                ))}
              </div>
              {breachMode && (
                <p className="mt-4 text-sm text-emerald-100">
                  Protected: the breach reveals ciphertext instead of individual salary values.
                </p>
              )}
            </div>
          </div>
        </section>

        <section className={glassCard}>
          <div className="mb-5 flex items-center gap-3">
            <Database className="h-6 w-6 text-violet-300" />
            <div>
              <h2 className="text-xl font-bold text-white">Encrypted employee vault</h2>
              <p className="text-sm text-slate-400">
                This view intentionally displays ciphertext previews instead of salaries.
              </p>
            </div>
          </div>

          {employees.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-700 p-8 text-center text-slate-400">
              No employee data yet. Add a protected salary record above.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[700px] text-left text-sm">
                <thead className="border-b border-white/10 text-xs uppercase tracking-wider text-slate-500">
                  <tr>
                    <th className="px-3 py-3">Employee</th>
                    <th className="px-3 py-3">Department</th>
                    <th className="px-3 py-3">Position</th>
                    <th className="px-3 py-3">Stored salary field</th>
                  </tr>
                </thead>
                <tbody>
                  {employees.map((employee) => (
                    <tr key={employee.id} className="border-b border-white/5">
                      <td className="px-3 py-4">
                        <p className="font-semibold text-white">{employee.name}</p>
                        <p className="text-xs text-slate-500">{employee.employee_id}</p>
                      </td>
                      <td className="px-3 py-4 text-slate-300">{employee.department}</td>
                      <td className="px-3 py-4 text-slate-300">{employee.position}</td>
                      <td className="px-3 py-4">
                        <code className="block max-w-[280px] truncate rounded-md bg-emerald-500/5 px-2 py-1 text-xs text-emerald-300">
                          {employee.encrypted_salary}
                        </code>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <footer className="py-10 text-center text-xs text-slate-500">
          PrivacyVault • Educational privacy-preserving analytics demonstration • CKKS simulation mode
        </footer>
      </section>
    </main>
  );
}

export default App;