"""
Homomorphic Encryption wrapper using Pyfhel
Implements CKKS scheme for approximate number arithmetic (salaries)
"""
from Pyfhel import Pyfhel
import numpy as np
import time
from typing import Tuple, List, Optional
from config import settings


class HomomorphicEncryption:
    """
    Homomorphic Encryption wrapper for PrivacyVault
    Uses CKKS scheme which supports addition and multiplication on encrypted real numbers
    """
    
    def __init__(self):
        """Initialize the HE context with CKKS parameters"""
        self.he = Pyfhel()
        
        # CKKS parameters for approximate arithmetic
        # Good for salary calculations (real numbers)
        self.he.context(
            scheme=settings.ENCRYPTION_SCHEME,
            poly_modulus_degree=settings.POLY_MOD_DEGREE,
            coeff_mod_bit_sizes=[60, 40, 40, 60],  # Modulus chain
            scale=settings.SCALE,
            functional_depth=2  # Support for multiple operations
        )
        
        # Generate keys
        self.he.keyGen()
        
        # Store context info for serialization
        self.context_info = {
            "scheme": settings.ENCRYPTION_SCHEME,
            "poly_modulus_degree": settings.POLY_MOD_DEGREE,
            "scale": settings.SCALE,
        }
    
    def encrypt_salary(self, salary: float) -> Tuple[str, dict]:
        """
        Encrypt a single salary value
        
        Args:
            salary: Salary value to encrypt
            
        Returns:
            Tuple of (encrypted_hex_string, context_info)
        """
        start_time = time.time()
        
        # Encrypt the salary
        encrypted = self.he.encrypt(salary)
        
        # Convert to bytes then to hex string for storage
        encrypted_bytes = encrypted.to_bytes()
        encrypted_hex = encrypted_bytes.hex()
        
        encryption_time = (time.time() - start_time) * 1000  # ms
        
        return encrypted_hex, {
            "encryption_time_ms": encryption_time,
            "context": self.context_info,
            "original_value_range": f"₹{salary:,.0f}",
        }
    
    def decrypt_salary(self, encrypted_hex: str) -> Tuple[float, dict]:
        """
        Decrypt a salary value
        
        Args:
            encrypted_hex: Hex string of encrypted data
            
        Returns:
            Tuple of (decrypted_value, metadata)
        """
        start_time = time.time()
        
        # Convert hex back to bytes
        encrypted_bytes = bytes.fromhex(encrypted_hex)
        
        # Create Pyfhel object from bytes
        encrypted = self.he.from_bytes(encrypted_bytes)
        
        # Decrypt
        decrypted = self.he.decrypt(encrypted)
        
        decryption_time = (time.time() - start_time) * 1000  # ms
        
        return float(decrypted), {
            "decryption_time_ms": decryption_time,
        }
    
    def add_encrypted(self, encrypted_hex1: str, encrypted_hex2: str) -> Tuple[str, dict]:
        """
        Add two encrypted values homomorphically
        
        Args:
            encrypted_hex1: First encrypted value (hex)
            encrypted_hex2: Second encrypted value (hex)
            
        Returns:
            Tuple of (encrypted_sum_hex, metadata)
        """
        start_time = time.time()
        
        # Convert hex to Pyfhel objects
        enc1_bytes = bytes.fromhex(encrypted_hex1)
        enc2_bytes = bytes.fromhex(encrypted_hex2)
        
        enc1 = self.he.from_bytes(enc1_bytes)
        enc2 = self.he.from_bytes(enc2_bytes)
        
        # Perform homomorphic addition
        encrypted_sum = enc1 + enc2
        
        # Convert result to hex
        sum_bytes = encrypted_sum.to_bytes()
        sum_hex = sum_bytes.hex()
        
        computation_time = (time.time() - start_time) * 1000  # ms
        
        return sum_hex, {
            "computation_time_ms": computation_time,
            "operation": "addition",
        }
    
    def compute_sum_encrypted(self, encrypted_salaries: List[str]) -> Tuple[str, dict]:
        """
        Compute sum of multiple encrypted salaries
        
        Args:
            encrypted_salaries: List of encrypted salary hex strings
            
        Returns:
            Tuple of (encrypted_sum_hex, metadata)
        """
        if not encrypted_salaries:
            raise ValueError("No encrypted salaries provided")
        
        start_time = time.time()
        
        # Convert all to Pyfhel objects
        encrypted_objects = []
        for enc_hex in encrypted_salaries:
            enc_bytes = bytes.fromhex(enc_hex)
            encrypted_objects.append(self.he.from_bytes(enc_bytes))
        
        # Sum all encrypted values
        total = encrypted_objects[0]
        for enc_obj in encrypted_objects[1:]:
            total = total + enc_obj
        
        # Convert to hex
        total_bytes = total.to_bytes()
        total_hex = total_bytes.hex()
        
        computation_time = (time.time() - start_time) * 1000  # ms
        
        return total_hex, {
            "computation_time_ms": computation_time,
            "operation": "sum",
            "employee_count": len(encrypted_salaries),
        }
    
    def compute_average_encrypted(self, encrypted_salaries: List[str]) -> Tuple[str, dict]:
        """
        Compute average of encrypted salaries
        
        For CKKS, we can multiply by scalar (1/n) after summing
        
        Args:
            encrypted_salaries: List of encrypted salary hex strings
            
        Returns:
            Tuple of (encrypted_average_hex, metadata)
        """
        if not encrypted_salaries:
            raise ValueError("No encrypted salaries provided")
        
        start_time = time.time()
        n = len(encrypted_salaries)
        
        # First compute sum
        sum_hex, _ = self.compute_sum_encrypted(encrypted_salaries)
        
        # Convert sum to Pyfhel object
        sum_bytes = bytes.fromhex(sum_hex)
        encrypted_sum = self.he.from_bytes(sum_bytes)
        
        # Multiply by 1/n (CKKS supports scalar multiplication)
        encrypted_avg = encrypted_sum * (1.0 / n)
        
        # Convert to hex
        avg_bytes = encrypted_avg.to_bytes()
        avg_hex = avg_bytes.hex()
        
        computation_time = (time.time() - start_time) * 1000  # ms
        
        return avg_hex, {
            "computation_time_ms": computation_time,
            "operation": "average",
            "employee_count": n,
        }
    
    def compute_weighted_average_encrypted(
        self, 
        encrypted_salaries: List[str], 
        weights: List[float]
    ) -> Tuple[str, dict]:
        """
        Compute weighted average of encrypted salaries
        
        Args:
            encrypted_salaries: List of encrypted salary hex strings
            weights: List of weights (must match length of salaries)
            
        Returns:
            Tuple of (encrypted_weighted_avg_hex, metadata)
        """
        if not encrypted_salaries:
            raise ValueError("No encrypted salaries provided")
        
        if len(encrypted_salaries) != len(weights):
            raise ValueError("Weights must match number of salaries")
        
        start_time = time.time()
        
        # Convert all to Pyfhel objects
        encrypted_objects = []
        for enc_hex in encrypted_salaries:
            enc_bytes = bytes.fromhex(enc_hex)
            encrypted_objects.append(self.he.from_bytes(enc_bytes))
        
        # Compute weighted sum
        weighted_sum = encrypted_objects[0] * weights[0]
        for enc_obj, weight in zip(encrypted_objects[1:], weights[1:]):
            weighted_sum = weighted_sum + (enc_obj * weight)
        
        # Divide by sum of weights
        total_weight = sum(weights)
        weighted_avg = weighted_sum * (1.0 / total_weight)
        
        # Convert to hex
        avg_bytes = weighted_avg.to_bytes()
        avg_hex = avg_bytes.hex()
        
        computation_time = (time.time() - start_time) * 1000  # ms
        
        return avg_hex, {
            "computation_time_ms": computation_time,
            "operation": "weighted_average",
            "employee_count": len(encrypted_salaries),
            "total_weight": total_weight,
        }
    
    def get_performance_metrics(self, num_samples: int = 10) -> dict:
        """
        Get performance metrics for encryption/decryption/computation
        
        Args:
            num_samples: Number of samples to average
            
        Returns:
            Dictionary with performance metrics
        """
        # Test data
        test_salaries = [50000, 75000, 100000, 60000, 90000]
        
        # Measure encryption time
        enc_times = []
        encrypted_list = []
        for salary in test_salaries:
            start = time.time()
            enc_hex, _ = self.encrypt_salary(salary)
            enc_times.append((time.time() - start) * 1000)
            encrypted_list.append(enc_hex)
        
        # Measure decryption time
        dec_times = []
        for enc_hex in encrypted_list:
            start = time.time()
            dec_val, _ = self.decrypt_salary(enc_hex)
            dec_times.append((time.time() - start) * 1000)
        
        # Measure computation time (sum)
        start = time.time()
        sum_hex, _ = self.compute_sum_encrypted(encrypted_list)
        sum_time = (time.time() - start) * 1000
        
        # Measure plaintext computation for comparison
        start = time.time()
        plaintext_sum = sum(test_salaries)
        plaintext_time = (time.time() - start) * 1000
        
        return {
            "avg_encryption_time_ms": np.mean(enc_times),
            "avg_decryption_time_ms": np.mean(dec_times),
            "encrypted_computation_time_ms": sum_time,
            "plaintext_computation_time_ms": plaintext_time,
            "overhead_ratio": sum_time / plaintext_time if plaintext_time > 0 else float('inf'),
            "encryption_scheme": settings.ENCRYPTION_SCHEME,
            "poly_modulus_degree": settings.POLY_MOD_DEGREE,
        }


# Global instance (in production, use dependency injection)
he_instance = HomomorphicEncryption()