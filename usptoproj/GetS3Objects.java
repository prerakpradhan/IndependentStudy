                                                    
import java.io.File;

import com.amazonaws.auth.BasicAWSCredentials;      
import com.amazonaws.services.s3.AmazonS3;          
import com.amazonaws.services.s3.AmazonS3Client;    
import com.amazonaws.services.s3.model.GetObjectRequest;

public class GetS3Objects {

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		BasicAWSCredentials awsCreds = new BasicAWSCredentials("*","*");
		AmazonS3 s3Client = new AmazonS3Client(awsCreds); 	                                                                                                                          
		String s3bucket="uspto-bigrams";        
		
		System.out.println("Starting download file1");	
		File file1=new File("outputm1.csv");
		s3Client.getObject( new GetObjectRequest(s3bucket, "bigrams/outputm1.csv"),file1); 
		
		System.out.println("Starting download file2");
		File file2=new File("outputm2.csv");
		s3Client.getObject(new GetObjectRequest(s3bucket, "bigrams/outputm2.csv"),file2); 
		
		System.out.println("Starting download file3");
		File file3=new File("outputm3.csv");
		s3Client.getObject(new GetObjectRequest(s3bucket, "bigrams/outputm3.csv"),file3);
		
		System.out.println("Starting download file4");
		File file4=new File("outputm4.csv");
		s3Client.getObject(new GetObjectRequest(s3bucket, "bigrams/outputm4.csv"),file4); 
		
		System.out.println( "Starting download file5");
		File file5=new File( "outputm5.csv");
		s3Client.getObject(new GetObjectRequest(s3bucket, "bigrams/outputm5.csv"),file5);  
		
		
		System.out.println("Downloads finish finished");                                                                                    

	}

}
