import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.HashSet;

public class CosineSim {
	
	public void runCosine() throws Exception{

		BufferedReader br =new BufferedReader(new FileReader(new File("/home/nishant/sample.txt")));
		String line;
	
		String prev="";
		Connection con=getDbConnection();
		ArrayList<String> patents=new ArrayList<String>();
		//HashSet<String> bigrams=new HashSet<String>();
		while((line=br.readLine()) != null){
			String[] clust_info=line.split("\t");
			String current = clust_info[1].substring(0,clust_info[1].lastIndexOf(':'));
						
			if (!current.equals(prev)){
				if(!prev.isEmpty()){
					//int[][] incidence=buildIncidenceMatrix(patents,bigrams,con);
					//double cos_sim=getCosineSimilarity(incidence);					
					//writeResults(cos_sim,prev);
					calculatePairwiseSimilarity(patents,prev,con);
					patents.clear();
					//bigrams.clear();
				}
				
				patents.add(clust_info[0]);
				//bigrams.addAll(getBigramsFromPatents(con,clust_info[0]));
				prev=current;
			}
			else{
				
				patents.add(clust_info[0]);
				//bigrams.addAll(getBigramsFromPatents(con,clust_info[0]));		
				prev=current;
			}
		}
		//int[][] incidence=buildIncidenceMatrix(patents,bigrams,con);
		//double cos_sim=getCosineSimilarity(incidence);					
		//writeResults(cos_sim,prev);
		calculatePairwiseSimilarity(patents,prev,con);
		con.close();
		br.close();
	}
	
	public int[][] buildIncidenceMatrix(ArrayList<String> patents, HashSet<String> bigrams, Connection con) throws Exception{
		int[][] incidence=new int[patents.size()][bigrams.size()];
		ArrayList<String> bgarray=new ArrayList<String>();
		bgarray.addAll(bigrams);
		
		int i=0;
		String query="select bigram,count from bigrams where patent_id=?";
		PreparedStatement stmt=con.prepareStatement(query);
		
		for(String patent: patents){
			//get list of bigrams for that patent and count	
			stmt.setString(1, patent);
			ResultSet rset=stmt.executeQuery();
			while(rset.next()){
				int index = bgarray.indexOf(rset.getString("bigram"));
				int count = Integer.parseInt(rset.getString("count"));
				incidence[i][index]=count;
			}
			i++;
			rset.close();
		}
		stmt.close();
		return incidence;
	}
	
	public double getCosineSimilarity(int[][] incidence){
		//double cosine_similarity=-10;
		if(incidence.length < 2)
			return -10;
		
		int cols=incidence[0].length;		
		int[] rowsum=new int[incidence.length];
		for(int i=0;i<incidence.length;i++){
			int sum=0;
			for(int j=0; j<incidence[i].length;j++)
				sum=(int) (sum+Math.pow(incidence[i][j],2));;
			rowsum[i]=sum;
		}
				
		/*
		for(int j=0; j<cols;j++){
			double temp=1;
			for (int i=0; i<incidence.length;i++)
				temp=temp*incidence[i][j]/rowsum[i];
			cosine_similarity=cosine_similarity+temp;
		}
		*/
		
		double temp=0;
		for(int i=0;i<cols;i++){
			temp=temp+incidence[0][i]*incidence[1][i];
		}

		for(int i=0;i<rowsum.length;i++)
			temp=temp/Math.sqrt(rowsum[i]);
			
		return temp;
		
		//return cosine_similarity;
	}
	
	public Connection getDbConnection(){
		try {
			Class.forName("com.mysql.jdbc.Driver");
			Connection con=DriverManager.getConnection("jdbc:mysql://localhost/uspto","nishant","datalab");
		    return con;
			
		} catch (ClassNotFoundException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
			System.exit(-1);
		}
		catch(SQLException e){
			e.printStackTrace();
			System.exit(-1);
		}
		return null;
		
	}
	
	public ArrayList<String> getBigramsFromPatents(Connection con, String patentid) throws Exception{
		String query="select bigram from bigrams where patent_id=?";
		PreparedStatement stmt=con.prepareStatement(query);
		stmt.setString(1, patentid);
		ResultSet rset=stmt.executeQuery();
		ArrayList<String> bigrams=new ArrayList<String>();
		while(rset.next())
			bigrams.add(rset.getString("bigram"));
		stmt.close();
		rset.close();
		return bigrams;
	}
	
	public void writeResults(double cos_sim, String patent1, String patent2,String cluster) throws Exception {
		File results=new File("results.txt");
		results.createNewFile();
		FileWriter fw=new FileWriter("results.txt",true);
		fw.write(cluster+"\t"+patent1+"\t"+patent2+"\t"+cos_sim+"\n");
		fw.close();
		
	}
	
	public void calculatePairwiseSimilarity(ArrayList<String> patents, String cluster, Connection con) throws Exception{
		
		for(int i=0; i<patents.size();i++){
			double cos_sim=-10;			
			ArrayList<String> patsubset=new ArrayList<String>();
			HashSet<String> bigrams=new HashSet<String>();
			bigrams.addAll(getBigramsFromPatents(con,patents.get(i)));
			patsubset.add(patents.get(i));
			for (int j=i+1;j<patents.size();j++){
				patsubset.add(patents.get(j));
				HashSet<String> newbigrams=new HashSet<String>();
				newbigrams.addAll(bigrams);
				newbigrams.addAll(getBigramsFromPatents(con,patents.get(j)));
				int[][] incidence = buildIncidenceMatrix(patsubset,newbigrams,con);
				cos_sim=getCosineSimilarity(incidence);
				writeResults(cos_sim,patsubset.get(0),patsubset.get(1),cluster);
				patsubset.remove(patsubset.size()-1);								
			}
		}
	}
	
	

}
