import { execFileSync } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const login = process.env.GITHUB_USERNAME || 'wenruifan';
const token = process.env.GH_CONTRIBUTIONS_TOKEN
  || process.env.GITHUB_TOKEN
  || execFileSync('gh', ['auth', 'token'], { encoding: 'utf8' }).trim();

if (!token) {
  throw new Error('A GitHub token is required to fetch contribution data.');
}

const to = new Date();
const from = new Date(to.getTime() - 365 * 24 * 60 * 60 * 1000);
const query = `
  query Contributions($login: String!, $from: DateTime!, $to: DateTime!) {
    user(login: $login) {
      contributionsCollection(from: $from, to: $to) {
        contributionCalendar {
          totalContributions
          weeks {
            firstDay
            contributionDays {
              date
              contributionCount
              contributionLevel
            }
          }
        }
        totalCommitContributions
        totalIssueContributions
        totalPullRequestContributions
        totalPullRequestReviewContributions
        restrictedContributionsCount
        commitContributionsByRepository(maxRepositories: 20) {
          repository {
            nameWithOwner
            url
          }
          contributions {
            totalCount
          }
        }
      }
    }
  }
`;

const response = await fetch('https://api.github.com/graphql', {
  method: 'POST',
  headers: {
    Accept: 'application/vnd.github+json',
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
    'User-Agent': 'wenrui-fan-academic-homepage',
  },
  body: JSON.stringify({
    query,
    variables: { login, from: from.toISOString(), to: to.toISOString() },
  }),
});

if (!response.ok) {
  throw new Error(`GitHub GraphQL request failed: ${response.status} ${response.statusText}`);
}

const payload = await response.json();
if (payload.errors?.length) {
  throw new Error(`GitHub GraphQL error: ${payload.errors.map(({ message }) => message).join('; ')}`);
}

const collection = payload.data?.user?.contributionsCollection;
if (!collection) {
  throw new Error(`GitHub user ${login} was not found.`);
}

const repositories = collection.commitContributionsByRepository
  .map(({ repository, contributions }) => ({
    name: repository.nameWithOwner,
    url: repository.url,
    commits: contributions.totalCount,
  }))
  .sort((a, b) => b.commits - a.commits);

const weeks = collection.contributionCalendar.weeks.map((week) => ({
  ...week,
  contributionDays: week.contributionDays.map((day) => ({
    ...day,
    weekday: new Date(`${day.date}T00:00:00Z`).getUTCDay(),
  })),
}));

const output = {
  schemaVersion: 1,
  login,
  profileUrl: `https://github.com/${login}`,
  generatedAt: to.toISOString(),
  from: from.toISOString(),
  to: to.toISOString(),
  totalContributions: collection.contributionCalendar.totalContributions,
  restrictedContributions: collection.restrictedContributionsCount,
  activity: {
    commits: collection.totalCommitContributions,
    pullRequests: collection.totalPullRequestContributions,
    issues: collection.totalIssueContributions,
    reviews: collection.totalPullRequestReviewContributions,
  },
  topRepositories: repositories,
  weeks,
};

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const outputPath = resolve(projectRoot, 'data/github_contributions.json');
await mkdir(dirname(outputPath), { recursive: true });
await writeFile(outputPath, `${JSON.stringify(output, null, 2)}\n`, 'utf8');

console.log(`Fetched ${output.totalContributions} GitHub contributions for ${login}.`);
