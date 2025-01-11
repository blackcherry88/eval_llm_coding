# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/01_em_torch_openai.ipynb.

# %% auto 0
__all__ = ['GMM']

# %% ../../nbs/01_em_torch_openai.ipynb 3
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.distributions.multivariate_normal import MultivariateNormal

# %% ../../nbs/01_em_torch_openai.ipynb 4
# There are many errors from naive openai generate code like
# not using scale_tril etc
class GMM(nn.Module):
    def __init__(self, n_components, n_features, low=-4.0, high=4.0):
        super(GMM, self).__init__()
        self.n_components = n_components
        self.n_features = n_features
        
        # Initialize parameters as trainable variables
        self.means = nn.Parameter(torch.empty(n_components, n_features).uniform_(low, high))
        self.scale_tril = nn.Parameter(torch.stack([torch.tril(torch.eye(n_features)) for _ in range(self.n_components)]))
        self.log_weights = nn.Parameter(torch.zeros(n_components))
        # print(f"{self.n_components}, {self.n_features} mean: {self.means} variances {self.covariances}")

    @property
    def covariances(self):
        return torch.matmul(self.scale_tril, self.scale_tril.transpose(1, 2))
    
    def _e_step(self, X):
        """Compute responsibilities (E-step)."""
        n_samples = X.shape[0]
        weights = torch.softmax(self.log_weights, dim=0)  # Normalize weights
        responsibilities = torch.zeros(n_samples, self.n_components)
        
        for k in range(self.n_components):
            # Ensure positive-definiteness of covariance matrices
            mvn = MultivariateNormal(self.means[k], scale_tril=self.scale_tril[k])
            responsibilities[:, k] = weights[k] * mvn.log_prob(X).exp()
            # print(f"K {k}: mean {self.means[k]} responsibilities{responsibilities[-10:, k]}")
        
        # Normalize responsibilities across components
        responsibilities /= responsibilities.sum(dim=1, keepdim=True)
        # print(f"responsibilities: {responsibilities[:10, :]}")
        return responsibilities


    def _m_step(self, X, responsibilities):
        """M step, compute the negative log-likelihood using responsibilities."""
        log_likelihood = 0
        for k in range(self.n_components):
            mvn = MultivariateNormal(self.means[k], scale_tril=self.scale_tril[k])
            log_prob = mvn.log_prob(X)  # Log probability for all points
            log_likelihood += responsibilities[:, k] * (log_prob + F.log_softmax(self.log_weights[k], dim=-1))

        # Negative log-likelihood
        return -log_likelihood.mean()


    def forward(self, X):
        responsibilities = self._e_step(X)
        return self._m_step(X, responsibilities)
    
    def predict(self, X):
        return self._e_step(X)

