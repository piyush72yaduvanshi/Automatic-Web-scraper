import { Users, Briefcase, Mail, Phone, Share2, CheckCircle, XCircle, Clock } from 'lucide-react';
import { useStats } from '../hooks/useStats';
import { useJobs } from '../hooks/useJobs';

const Dashboard = () => {
  const { data: stats, isLoading: statsLoading } = useStats();
  const { data: recentJobs, isLoading: jobsLoading } = useJobs({ page: 1, page_size: 5 });
  
  const statCards = [
    {
      title: 'Total Leads',
      value: stats?.total_leads || 0,
      icon: Users,
      color: 'bg-blue-500',
    },
    {
      title: 'Discovery Jobs',
      value: stats?.total_jobs || 0,
      icon: Briefcase,
      color: 'bg-purple-500',
    },
    {
      title: 'Emails Found',
      value: stats?.emails_found || 0,
      icon: Mail,
      color: 'bg-green-500',
    },
    {
      title: 'Phones Found',
      value: stats?.phones_found || 0,
      icon: Phone,
      color: 'bg-orange-500',
    },
    {
      title: 'Social Profiles',
      value: stats?.social_profiles_found || 0,
      icon: Share2,
      color: 'bg-pink-500',
    },
  ];
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'FAILED':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'RUNNING':
      case 'QUEUED':
        return <Clock className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return null;
    }
  };
  
  if (statsLoading || jobsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }
  
  return (
    <div className="px-4 sm:px-0">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.title} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">
                    {stat.value.toLocaleString()}
                  </p>
                </div>
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Job Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-green-50 rounded-lg p-4 border border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-green-600">Completed</p>
              <p className="text-xl font-bold text-green-700">{stats?.jobs_completed || 0}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>
        
        <div className="bg-red-50 rounded-lg p-4 border border-red-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-red-600">Failed</p>
              <p className="text-xl font-bold text-red-700">{stats?.jobs_failed || 0}</p>
            </div>
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
        </div>
        
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-600">Running</p>
              <p className="text-xl font-bold text-blue-700">{stats?.jobs_running || 0}</p>
            </div>
            <Clock className="w-8 h-8 text-blue-500" />
          </div>
        </div>
      </div>
      
      {/* Recent Jobs */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Discovery Jobs</h2>
        </div>
        <div className="p-6">
          {recentJobs && recentJobs.items.length > 0 ? (
            <div className="space-y-4">
              {recentJobs.items.map((job) => (
                <div key={job.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-gray-900">{job.search_query}</p>
                      {getStatusIcon(job.status)}
                    </div>
                    <p className="text-sm text-gray-500">{job.location}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">
                      {job.total_found} found
                    </p>
                    <p className="text-sm text-gray-500">
                      {job.total_enriched} enriched
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No jobs yet. Start by creating a discovery job.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
